"""Sends a job title + description of actual duties to Claude and gets back
a task-by-task AI-automation exposure assessment plus a concrete reskilling
roadmap.
"""
from typing import Literal

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

RiskLevel = Literal["low", "moderate", "high", "very_high"]


class TaskExposure(BaseModel):
    task: str
    exposure: RiskLevel
    reasoning: str


class RoadmapItem(BaseModel):
    action: str  # a specific skill, certification, or adjacent role
    why: str  # tied to which current task(s) this protects against or moves away from


class RiskAssessment(BaseModel):
    overall_summary: str
    overall_risk: RiskLevel
    tasks: list[TaskExposure]
    roadmap: list[RoadmapItem]


SYSTEM_PROMPT = """You are a career-risk analyst. Given a job title and a \
description of someone's actual day-to-day duties, assess how exposed each \
specific task is to AI automation - not the job title in general, the actual \
tasks named. Ground every exposure rating in concrete reasoning: name real \
tools/capabilities that automate or don't automate that specific task today, \
not speculation about the future.

Then produce a reskilling roadmap of 3-5 concrete actions (specific skills, \
certifications, or adjacent roles - never generic advice like "learn to \
code" or "develop soft skills"). Tie each roadmap item to which of their \
named tasks it protects or transitions them away from.

overall_risk should reflect the weighted reality of their role: a mix of \
high-exposure routine tasks and low-exposure judgment/relationship tasks is \
"moderate", not an average."""


def assess_role(job_title: str, duties: str) -> RiskAssessment:
    client = anthropic.Anthropic()

    response = client.messages.parse(
        model="claude-opus-5",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Job title: {job_title}\n\nTypical duties: {duties}",
        }],
        output_format=RiskAssessment,
    )

    return response.parsed_output
