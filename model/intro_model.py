import csv
import os
from typing import Literal, Optional, TypedDict

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END,START

from typing import Optional
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
llm = ChatOllama(
    model='qwen2.5:7b',
    base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
)
class is_intro(BaseModel):
    message_type:Literal['intro','simple']=Field(description="Return 'intro' if the message is a self-introduction "
            "containing information about the person's name, location, "
            "education, college, hobbies, etc. "
            "Return 'simple' if it is normal conversation.")

class Extract(BaseModel):
    name: str = Field(description="Full name of the student")
    address: str = Field(description="Address of the student, including village/town and district")
    school_of_sec: str = Field(description="Name of the school from where the student passed the secondary (Class 10) examination")
    board_of_sec: str = Field(description="Name of the board affiliated to the school for the secondary examination (e.g. WBBSE)")
    percentage_sec: float = Field(description="Percentage of marks obtained in the secondary examination")
    marks_obtained_sec: int = Field(
        description=(
            "The exact marks obtained by the student in the secondary (Class 10) "
            "examination. Extract only the obtained marks as an integer. "
            "For example, if the message says '645 out of 700', return 645."
        )
    )

    total_marks_sec: int = Field(
        description=(
            "The maximum total marks for the secondary (Class 10) examination. "
            "Extract only the total marks as an integer. "
            "For example, if the message says '645 out of 700', return 700."
        )
    )
    year_of_sec: int = Field(description="Year in which the student passed the secondary examination")

    school_of_hs: str = Field(description="Name of the school from where the student passed the higher secondary (Class 12) examination")
    board_of_hs: str = Field(description="Name of the board/council affiliated to the school for the higher secondary examination (e.g. WBCHSE)")
    percentage_hs: float = Field(description="Percentage of marks obtained in the higher secondary examination")
    marks_obtained_hs: int = Field(
    description=(
        "The exact marks obtained by the student in the higher secondary "
        "(Class 12) examination. Extract only the obtained marks as an integer. "
        "For example, if the message says '447 out of 500', return 447."
    )
)

    total_marks_hs: int = Field(
        description=(
            "The maximum total marks for the higher secondary (Class 12) examination. "
            "Extract only the total marks as an integer. "
            "For example, if the message says '447 out of 500', return 500."
        )
    )
    year_of_hs: int = Field(description="Year in which the student passed the higher secondary examination")

    entrance_exam: str = Field(description="Name of the entrance examination appeared for, e.g. West Bengal Joint Entrance Examination (WBJEE)")
    entrance_exam_year: int = Field(description="Year in which the entrance examination was appeared for")
    entrance_exam_rank: int = Field(description="Rank obtained in the entrance examination")

    college_name: str = Field(description="Name of the college/institute where admission was secured through counselling")
    department: str = Field(description="Name of the department/branch admitted into through counselling")

    hobbies: Optional[str] = Field(default=None, description="Hobbies or interests of the student, if mentioned")
    extracurricular_activities: Optional[str] = Field(default=None, description="Extracurricular activities the student is or was involved in, e.g. sports, clubs, competitions, volunteering, if mentioned")


extractor_llm = llm.with_structured_output(Extract)
# classifier_llm = llm.with_structured_output(is_intro)
# intro =''' My name is Sarthak Bhattacharjee. I am from Sodepur, North 24 Parganas . I passed secondary examination from Krishnagar Collegiate School affiliated to West Bengal Board of Secondary Education with six hundred sixty one marks out of seven hundred in year 2023. I passed higher secondary from Krishnagar Collegiate School affiliated to West Bengal Council of Higher Secondary Education with three hundred eighteen marks out of five hundred in year 2025. I appeared for West Bengal Joint Entrance Examination in year 2026 and obtained general merit rank of one thousand eight hundred twenty five. Then I appeared for online councelling of West Bengal Joint Entrance Examination Board and got an opportunity to study in Information Technology department in Jalpaiguri Government Engineering College, Autonomous. My hobby is playing cricket. My extracurricular activities includes playing chess.'''

# result = extractor_llm.invoke(intro)
# print(result)
class IntroState(TypedDict):
    intro:str
    extracted_result:Extract
    saved_at_csv:str
def extract(state:IntroState):
    intro = state['intro']
    result = extractor_llm.invoke(intro)
    return {'extracted_result':result}
import csv
import os

def save_csv(state: IntroState):
    result = state["extracted_result"]

    row = [
        result.name,
        result.address,
        result.school_of_sec,
        result.board_of_sec,
        result.percentage_sec,
        result.marks_obtained_sec,
        result.total_marks_sec,
        result.year_of_sec,
        result.school_of_hs,
        result.board_of_hs,
        result.percentage_hs,
        result.marks_obtained_hs,
        result.total_marks_hs,
        result.year_of_hs,
        result.entrance_exam,
        result.entrance_exam_year,
        result.entrance_exam_rank,
        result.college_name,
        result.department,
        result.hobbies,
        result.extracurricular_activities
    ]

    columns = [
        "name",
        "address",
        "school_of_sec",
        "board_of_sec",
        "percentage_sec",
        "marks_obtained_sec",
        "total_marks_sec",
        "year_of_sec",
        "school_of_hs",
        "board_of_hs",
        "percentage_hs",
        "marks_obtained_hs",
        "total_marks_hs",
        "year_of_hs",
        "entrance_exam",
        "entrance_exam_year",
        "entrance_exam_rank",
        "college_name",
        "department",
        "hobbies",
        "extracurricular_activities"
    ]

    file_exists = os.path.exists("students.csv")

    with open("students.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(columns)

        writer.writerow(row)

    return {
        "saved_at_csv": "students.csv"
    }

graph = StateGraph(IntroState)

graph.add_node('extract',extract)
graph.add_node('save_csv',save_csv)
graph.add_edge(START,'extract')
graph.add_edge('extract','save_csv')
graph.add_edge('extract',END)

intro_workflow = graph.compile()
# result = intro_workflow.invoke({ "intro":intro})
# print(result)