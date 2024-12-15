from typing import List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.document_loaders import PyPDFLoader
from langchain.output_parsers import PydanticOutputParser
from langchain.text_splitter import CharacterTextSplitter
from pydantic import BaseModel
from app.schemas.user_story import UserStory

# Pydantic model for User Stories
class UserStories(BaseModel):
    user_stories: List[UserStory]

# Pydantic model for Test Cases
class TestCase(BaseModel):
    test_case_id: str
    description: str
    preconditions: List[str]
    steps: List[str]
    expected_result: str

# Class for generating User Stories
class UserStoryGenerator:
    def __init__(self, model="gpt-4", temperature=0.7):
        """
        Initializes the UserStoryGenerator with a shared LLM instance.
        :param model: The language model to use (default: GPT-4).
        :param temperature: The creativity/variability of the output (default: 0.7).
        """
        self.llm = ChatOpenAI(temperature=temperature, model=model)

    def extract_text_from_pdf(self, pdf_path: str) -> list:
        """
        Extracts text from a PDF document and splits it into chunks for processing.
        :param pdf_path: Path to the PDF file.
        :return: List of text chunks extracted from the PDF.
        """
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        text = ""
        for doc in documents:
            text += doc.page_content

        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = text_splitter.split_text(text)
        return chunks

    def generate_user_stories(self, requirement_chunks: list) -> dict:
        """
        Generates user stories from requirement chunks and formats them according to the UserStory Pydantic model.
        """
        prompt_template = """
        You are a software analyst. Based on the following requirement text, extract key user stories and define acceptance criteria for each:
        Requirement Text: {requirement_text}
        {format_instructions}
        """

        parser = PydanticOutputParser(pydantic_object=UserStories)

        prompt = PromptTemplate(
            input_variables=["requirement_text", "format_instructions"],
            template=prompt_template,
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)

        user_stories = {}

        for i, chunk in enumerate(requirement_chunks):
            print(f"Processing chunk {i + 1}/{len(requirement_chunks)}...")

            result = chain.run(
                requirement_text=chunk,
                format_instructions=parser.get_format_instructions(),
            )

            parsed_result = parser.parse(result)
            print(parsed_result)

            user_stories[f"chunk_{i + 1}"] = parsed_result

        return user_stories

# Class for generating Test Cases
class TestCaseGenerator:
    def __init__(self, model="gpt-4", temperature=0.7):
        """
        Initializes the TestCaseGenerator with a shared LLM instance.
        :param model: The language model to use (default: GPT-4).
        :param temperature: The creativity/variability of the output (default: 0.7).
        """
        self.llm = ChatOpenAI(temperature=temperature, model=model)

    def generate_test_cases(self, user_story: str, acceptance_criteria: str) -> dict:
        """
        Generates test cases from the user story and acceptance criteria.
        """
        prompt_template = """
        You are a QA analyst. Based on the following user story and acceptance criteria, generate detailed test cases.
        Include all relevant information: preconditions, test steps, expected results, and data requirements.
        Split functional and non-functional test case generation, and ensure that each set of test cases is appropriately categorized.
        User Story: {user_story}
        Acceptance Criteria:
        {acceptance_criteria}
        
        {format_instructions}
        """

        # Pydantic output parser for TestCase
        parser = PydanticOutputParser(pydantic_object=TestCase)

        # Define the prompt template
        prompt = PromptTemplate(
            input_variables=["user_story", "acceptance_criteria", "format_instructions"],
            template=prompt_template,
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)

        # Generate test case
        result = chain.run(
            user_story=user_story,
            acceptance_criteria=acceptance_criteria,
        )

        # Parse the result into structured test case format
        parsed_result = parser.parse(result)

        return parsed_result


if __name__ == "__main__":
    pdf_path = "app\\src\\BRD - HRMS.pdf"

    # Initialize the UserStoryGenerator
    user_story_generator = UserStoryGenerator(model="gpt-4", temperature=0.7)

    # Extract text from the PDF and split into chunks
    requirement_chunks = user_story_generator.extract_text_from_pdf(pdf_path)

    # Generate user stories from the extracted chunks
    user_stories = user_story_generator.generate_user_stories(requirement_chunks)

    # Print or save the generated user stories
    for chunk_id, story in user_stories.items():
        print(f"User Story for {chunk_id}: {story}")

    # Example: Generate test cases for a user story and acceptance criteria
    test_case_generator = TestCaseGenerator(model="gpt-4", temperature=0.7)

    # Example user story and acceptance criteria
    example_user_story = "As a user, I want to log into the system using my email and password."
    example_acceptance_criteria = "The user must be able to log in with a valid email and password."

    test_case = test_case_generator.generate_test_cases(example_user_story, example_acceptance_criteria)
    
    print(f"Test Case: {test_case}")
