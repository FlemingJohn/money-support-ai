from app.assistant.services.PromptBuilder import PromptBuilder
from app.common.services.TemplateRenderer import TemplateRenderer
from tests.support.SampleData import SampleData


class PromptBuilderTest:
    sample_data = SampleData()

    def make_builder(self) -> PromptBuilder:
        return PromptBuilder(TemplateRenderer(self.sample_data.make_configuration().prompts_folder))

    def build(self, learned_rules: list[str] | None = None) -> str:
        return self.make_builder().build(self.sample_data.make_faqs(), self.sample_data.make_settings(), learned_rules)

    def test_lists_the_faqs_in_number_order(self) -> None:
        prompt = self.build()
        assert prompt.index("1. How do I check my transfer's status?") < prompt.index("2. When will my money arrive?")
        assert "Log in and open the transfer." in prompt

    def test_fills_in_the_assistant_name(self) -> None:
        assert self.build().startswith("# Role\n\nYou are Money Support Agent,")

    def test_hands_off_with_the_tool_and_names_the_sentence_it_says(self) -> None:
        prompt = self.build()
        assert "use the handOffToHuman tool straight away, without saying anything yourself" in prompt
        assert "inDanger when the caller or someone else is in danger" in prompt
        assert f'"{self.sample_data.hand_off_sentence}"' in prompt

    def test_never_mentions_transferring_the_call(self) -> None:
        prompt = self.build()
        assert "transferCall" not in prompt
        assert "Europe/London" not in prompt

    def test_adds_learned_rules_at_the_end_so_the_start_stays_cached(self) -> None:
        prompt = self.build(["Fees are never in scope."])
        assert prompt.index("# Rules learned from reviews") > prompt.index("# Knowledge")
        assert "- Fees are never in scope." in prompt

    def test_leaves_out_the_learned_rules_section_when_there_are_none(self) -> None:
        assert "# Rules learned from reviews" not in self.build()
