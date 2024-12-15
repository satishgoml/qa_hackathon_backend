from typing import List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


# Pydantic model for Test Cases
class TestCase(BaseModel):
    name :str = Field(..., description="Name of the test case")
    description: str = Field(
        ..., description="A brief description of what the test case validates or checks"
    )
    preconditions: str = Field(
        ...,
        description="List of conditions or assumptions that must be true before the test case can be executed",
    )
    steps: str = Field(
        ..., description="Step-by-step instructions to execute the test case"
    )
    expected_result: str = Field(
        ...,
        description="The expected outcome or behavior once the test case steps are completed",
    )


class TestCases(BaseModel):
    test_cases: List[TestCase] = Field(
        ..., description="List of test cases generated from the user story"
    )


# Class for generating Test Cases
class TestCaseGenerator:
    def __init__(self, model="gpt-4", temperature=0.7):
        """
        Initializes the TestCaseGenerator with a shared LLM instance.

        :param model: The language model to use (default: GPT-4). Options like GPT-3.5, GPT-4, or other variants can be used.
        :param temperature: The creativity or randomness in the output (default: 0.7). A higher value generates more varied outputs.
        """
        self.llm = ChatOpenAI(temperature=temperature, model=model)

    def generate_test_cases(self, user_story: str, acceptance_criteria: str) -> dict:
        """
        Generates detailed test cases based on the user story and acceptance criteria.
        This method prompts a language model to analyze the user story and acceptance criteria
        and generate test cases that include functional and non-functional tests, preconditions,
        test steps, and expected results.

        :param user_story: A description of the user story outlining the feature or functionality to be tested.
        :param acceptance_criteria: A description of the conditions that must be met for the user story to be considered complete.
        :return: A structured test case based on the input user story and acceptance criteria.
        """
        prompt_template = """
        You are a QA analyst. Based on the following user story and acceptance criteria, generate detailed test cases as an array.
        Include all relevant information: preconditions, test steps, expected results, and data requirements.
        Split functional and non-functional test case generation, and ensure that each set of test cases is appropriately categorized.
        
        User Story: {user_story}
        Acceptance Criteria:
        {acceptance_criteria}
        
        {format_instructions}
        """

        # Pydantic output parser for TestCase
        parser = PydanticOutputParser(pydantic_object=TestCases)

        # Define the prompt template
        prompt = PromptTemplate(
            input_variables=[
                "user_story",
                "acceptance_criteria",
                "format_instructions",
            ],
            template=prompt_template,
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)

        # Generate test case using the chain
        result = chain.run(
            user_story=user_story,
            acceptance_criteria=acceptance_criteria,
            format_instructions=parser.get_format_instructions(),
        )

        # Parse the result into a structured test case format
        parsed_result = parser.parse(result)

        return parsed_result


if __name__ == "__main__":
    # Example user story and acceptance criteria
    example_user_story = (
        "As a user, I want to log into the system using my email and password, "
        "so that I can access my account securely."
    )
    example_acceptance_criteria = (
        "The user must be able to log in with a valid email and password. "
        "If the credentials are incorrect, an error message should appear."
    )

    # Initialize the TestCaseGenerator
    test_case_generator = TestCaseGenerator(model="gpt-4o", temperature=0.7)

    # Generate test cases based on the user story and acceptance criteria
    test_case = test_case_generator.generate_test_cases(
        example_user_story, example_acceptance_criteria
    )

    # Print the generated test case
    print(f"Test Case: {test_case}")
