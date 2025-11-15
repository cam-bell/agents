from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel
from typing import List


class ClassSpec(BaseModel):
    name: str
    responsibility: str

class ModuleSchema(BaseModel):
    module_name: str
    purpose: str
    classes: List[ClassSpec]
    dependencies: List[str]

class MultipleModules(BaseModel):
    modules: List[ModuleSchema]


@CrewBase
class EngineeringTeam():
    """EngineeringTeam crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],
            verbose=True,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=3 
        )
    
    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
        )
    
    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=3 
        )
    @agent
    def code_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['code_reviewer'],
            verbose=True,
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'],
            output_pydantic=MultipleModules,
        )

    @task
    def implementation_task(self) -> Task:
        return Task(
            config=self.tasks_config['implementation_task'],
        )   

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config['review_task'],
        )
    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'],
        )
    
    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the research crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )