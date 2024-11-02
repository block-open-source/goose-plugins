def create_analysis_prompt(analysis_type: str, **kwargs) -> str:
    """Create a prompt for various types of analysis."""
    prompts = {
        "structured": lambda p: f"""
            Perform a structured analysis of the following problem using the MECE principle:
            {p}
            Return the results as a JSON string with the following structure:
            {{
                "problem": "Brief restatement of the problem",
                "categories": [
                    {{
                        "name": "Category Name",
                        "elements": ["Element 1", "Element 2", ...],
                        "analysis": "Brief analysis of this category"
                    }},
                    ...
                ],
                "conclusion": "Overall conclusion based on the structured analysis"
            }}
        """,
        "request": lambda s: f"""
            Analyze the user statement: {s}
            If you need to immediately clarify something and it's something
            short and simple, respond with your question(s).
            If you need multiple questions, you can ask multiple questions.
            Please bullet point your questions.
            Limit your response to 5 questions.
        """,
        "solutions": lambda s: f"""
            Analyze the user statement: {s}
            Consider the existing message history and provide a well thought out response.
            Provide one or more potential solutions to the problem.
            Limit your response to 5 solutions.
        """,
        "stakeholder": lambda p: f"""
            Analyze the following problem statement and identify key stakeholders:
            {p}
            For each stakeholder, determine their interests and potential impacts.
        """,
        "future_scenarios": lambda p, t: f"""
            Based on the following problem statement and time horizon, generate potential future scenarios:
            Problem: {p}
            Time Horizon: {t}
            
            Consider various factors such as technological advancements, societal changes, 
            environmental impacts, and potential policy shifts.
            
            Return the results as a JSON string with scenarios including name, description,
            key factors, and potential outcomes.
            Generate at least 3 distinct scenarios.
        """,
        "system_mapping": lambda p: f"""
            Based on the following problem statement, create a high-level system map:
            {p}
            
            Identify key components, their relationships, and potential feedback loops.
            Return results as JSON with components and feedback loops.
        """,
        "risk": lambda p, s: f"""
            Perform a risk assessment for the following problem and proposed solution:
            Problem: {p}
            Proposed Solution: {s}
            
            Identify potential risks, their likelihood, impact, and possible mitigation strategies.
            Return results as JSON with detailed risk assessments.
        """,
        "ethical": lambda p, s: f"""
            Perform an ethical analysis for the following problem and proposed solution:
            Problem: {p}
            Proposed Solution: {s}
            
            Consider various ethical frameworks and principles, potential ethical dilemmas,
            and the impact on different stakeholders.
            Return results as JSON with ethical considerations and overall assessment.
        """
    }
    return prompts[analysis_type](**kwargs)