import logging
from datetime import UTC, datetime

from livekit.agents import AgentSession, CloseEvent, CloseReason, JobContext

from app.backend.clients.BackendClient import BackendClient
from app.backend.exceptions.BackendRequestError import BackendRequestError
from app.backend.models.PublishedAgent import PublishedAgent
from app.handoff.catalogs.HandOffReasonCatalog import HandOffReasonCatalog
from app.handoff.services.HandOffGraph import HandOffGraph
from app.voice.actions.LiveCallActions import LiveCallActions
from app.voice.factories.CallRecordFactory import CallRecordFactory
from app.voice.factories.SessionFactory import SessionFactory
from app.voice.factories.VoiceAgentFactory import VoiceAgentFactory
from app.voice.services.CallReportBuilder import CallReportBuilder
from app.voice.services.CallTimer import CallTimer
from app.voice.services.SilenceWatcher import SilenceWatcher
from app.voice.state.CallRecord import CallRecord

logger = logging.getLogger(__name__)


class CallHandler:
    def __init__(
        self,
        backend_client: BackendClient,
        session_factory: SessionFactory,
        voice_agent_factory: VoiceAgentFactory,
        call_record_factory: CallRecordFactory,
        call_report_builder: CallReportBuilder,
        hand_off_graph: HandOffGraph,
        reason_catalog: HandOffReasonCatalog,
    ) -> None:
        self.backend_client = backend_client
        self.session_factory = session_factory
        self.voice_agent_factory = voice_agent_factory
        self.call_record_factory = call_record_factory
        self.call_report_builder = call_report_builder
        self.hand_off_graph = hand_off_graph
        self.reason_catalog = reason_catalog

    async def handle(self, job_context: JobContext) -> None:
        await job_context.connect()
        caller = await job_context.wait_for_participant()
        call_record = self.call_record_factory.make(job_context.room.name, caller)
        published_agent = await self.backend_client.get_published_agent()
        session = self.session_factory.make(published_agent.settings.agent)
        call_actions = LiveCallActions(session, call_record, published_agent.settings.hand_off.hand_off_sentence, self.hand_off_graph, self.reason_catalog)
        self.watch_call(job_context, session, call_record, call_actions, published_agent)
        agent = self.voice_agent_factory.make(published_agent.prompt_content, call_actions)
        await session.start(agent, room=job_context.room, room_options=self.session_factory.make_room_options(call_record.channel))
        await self.report_start(call_record)
        session.say(published_agent.settings.agent.greeting)

    def watch_call(self, job_context: JobContext, session: AgentSession, call_record: CallRecord, call_actions: LiveCallActions, published_agent: PublishedAgent) -> None:
        agent_settings = published_agent.settings.agent
        silence_watcher = SilenceWatcher(session, call_actions, agent_settings.silence_seconds)
        silence_watcher.watch()
        timer = CallTimer().start(agent_settings.longest_call_minutes, call_actions)

        def handle_close(event: CloseEvent) -> None:
            timer.cancel()
            silence_watcher.stop()
            call_record.end("error" if event.reason == CloseReason.ERROR else "callerHungUp")
            job_context.shutdown()

        session.on("close", handle_close)
        job_context.add_shutdown_callback(lambda: self.report_finish(session, call_record))

    async def report_start(self, call_record: CallRecord) -> None:
        try:
            await self.backend_client.report_call_started(self.call_report_builder.build_start(call_record))
        except BackendRequestError as error:
            logger.warning("The call start was not reported: %s", error.message)

    async def report_finish(self, session: AgentSession, call_record: CallRecord) -> None:
        report = self.call_report_builder.build(call_record, session.history.items, datetime.now(UTC))
        try:
            await self.backend_client.report_call_finished(report)
        except BackendRequestError as error:
            logger.error("The finished call %s was not reported: %s", call_record.call_id, error.message)
