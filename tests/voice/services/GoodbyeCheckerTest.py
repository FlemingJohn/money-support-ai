from livekit.agents import ChatContext

from app.voice.services.GoodbyeChecker import GoodbyeChecker


class GoodbyeCheckerTest:
    checker = GoodbyeChecker()

    def make_items(self, agent_line: str, caller_line: str):
        history = ChatContext.empty()
        history.add_message(role="assistant", content=agent_line)
        history.add_message(role="user", content=caller_line)
        return history.items

    def test_ends_after_the_closing_question_and_a_goodbye(self) -> None:
        assert self.checker.can_end_call(self.make_items("Is there anything else I can help with?", "No, that's everything, thanks. Bye!"))

    def test_ends_on_a_plain_no_thanks(self) -> None:
        assert self.checker.can_end_call(self.make_items("Anything else today?", "No thanks."))

    def test_keeps_the_call_when_the_agent_has_not_asked(self) -> None:
        assert not self.checker.can_end_call(self.make_items("Log in and open the transfer.", "Bye!"))

    def test_keeps_the_call_when_the_caller_is_cut_off(self) -> None:
        assert not self.checker.can_end_call(self.make_items("Does that help? Anything else?", "No. No, that's"))
