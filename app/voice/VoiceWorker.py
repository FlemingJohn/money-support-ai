from livekit.agents import AgentServer, JobContext, cli

from app.configuration.AppConfiguration import AppConfiguration
from app.voice.VoiceContainer import VoiceContainer

configuration = AppConfiguration()
server = AgentServer()


@server.rtc_session(agent_name=configuration.agent_name)
async def handle_call(job_context: JobContext) -> None:
    container = VoiceContainer.from_configuration(configuration)
    await container.call_handler.handle(job_context)
    job_context.add_shutdown_callback(container.close)


if __name__ == "__main__":
    cli.run_app(server)
