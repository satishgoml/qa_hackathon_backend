import json
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.document_loaders import PyPDFLoader
from langchain.output_parsers import PydanticOutputParser
from langchain.text_splitter import CharacterTextSplitter
from pocketbase import PocketBase
from pydantic import BaseModel
from app.schemas.user_story import UserStory


class UserStories(BaseModel):
    """
    A Pydantic model to hold a collection of user stories.
    """

    user_stories: List[UserStory]


class UserStoryGenerator:
    """
    A class to extract text from a PDF and generate user stories based on the requirements.
    """

    def __init__(self, pb: PocketBase, model="gpt-4o-mini", temperature=0.7):
        """
        Initializes the UserStoryGenerator with a shared LLM instance.

        :param model: The language model to use (default: GPT-4).
        :param temperature: The creativity/variability of the output (default: 0.7).
        """
        self.llm = ChatOpenAI(temperature=temperature, model=model)
        self.pb = pb

    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """
        Extracts text from a PDF document and splits it into manageable chunks for processing.

        :param pdf_path: Path to the PDF file.
        :return: List of text chunks extracted from the PDF.
        """
        # Use Langchain's PyPDFLoader to extract text from PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # Combine all the extracted text from each page into a single string
        text = "".join(doc.page_content for doc in documents)

        # Use Langchain's CharacterTextSplitter to split the text into chunks
        text_splitter = CharacterTextSplitter(
            separator="\n",  # Define a suitable separator based on PDF structure
            chunk_size=1000,  # Define the chunk size in terms of characters
            chunk_overlap=10,  # Define how much overlap you want between chunks
        )
        chunks = text_splitter.split_text(text)
        return chunks

    def process_chunk(
        self, chunk: str, parser: PydanticOutputParser, chain: LLMChain
    ) -> List[UserStory]:
        """
        Processes a single chunk of text to generate user stories.

        :param chunk: A text chunk to process.
        :param parser: The output parser for the UserStory model.
        :param chain: The LLM chain to process the chunk.
        :return: A list of user stories for the given chunk.
        """
        try:
            # Run the LLM chain to generate the user story based on the requirement text
            result = chain.run(
                requirement_text=chunk,
                format_instructions=parser.get_format_instructions(),
            )

            # Parse the result into structured user story using the output parser
            parsed_result = parser.parse(result)

            return parsed_result.user_stories
        except Exception as e:
            print(f"Error processing chunk: {e}")
            return []

    def generate_user_stories(
        self, requirement_chunks: List[str],
        project_id: str,
        user_id : str
    ) -> List[UserStory]:
        """
        Generates user stories and saves them to PocketBase.
        """
        prompt_template = """
        You are a software analyst. Based on the following requirement text, extract key user stories and define acceptance criteria for each:
        
        If you encounter a section that doesn't contain user stories, return an empty list of user stories.
        
        Document Chunk: {requirement_text}
        {format_instructions}
        """

        parser = PydanticOutputParser(pydantic_object=UserStories)
        prompt = PromptTemplate(
            input_variables=["requirement_text", "format_instructions"],
            template=prompt_template,
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        user_stories = []

        with ThreadPoolExecutor() as executor:
            future_to_chunk = {
                executor.submit(self.process_chunk, chunk, parser, chain): chunk
                for chunk in requirement_chunks
            }

            for future in as_completed(future_to_chunk):
                try:
                    chunk_user_stories = future.result()
                    for story in chunk_user_stories:
                        # Prepare data for PocketBase
                        data = {
                            "title": story.title,
                            "description": story.description,
                            "acceptance_criteria": story.acceptance_criteria,
                            "priority": story.priority.value,
                            "story_points": story.story_points,
                            "status": story.status.value,
                            "project": project_id,
                            "user": user_id,
                        }
                        # Insert into PocketBase
                        self.pb.collection("user_story").create(data)
                        user_stories.append(story)

                except Exception as e:
                    print(f"Error in thread: {e}")

        return user_stories


if __name__ == "__main__":
    pdf_path = "app\src\BRD - HRMS.pdf"

    # Initialize the UserStoryGenerator
    user_story_generator = UserStoryGenerator(model="gpt-4o", temperature=0.7)

    # Extract text from PDF and split it into chunks
    print("Extracting text from PDF...")
    requirement_chunks = user_story_generator.extract_text_from_pdf(pdf_path)

    # Generate user stories from the extracted chunks
    print("Generating user stories from requirements...")
    user_stories = user_story_generator.generate_user_stories(requirement_chunks)

    # Print the final user stories
    print(json.dumps([story.model_dump() for story in user_stories], indent=4))

    # print the length of the user_stories list
    print("Length of user_stories list:", len(user_stories))

    # Now for each user story, generate test cases
