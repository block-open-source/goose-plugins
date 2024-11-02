from goose.toolkit.base import tool
from ..utils.analysis_utils import create_analysis_prompt

class AnalysisTools:
    @tool
    def structured_analysis(self, problem: str) -> str:
        """
        Perform a structured analysis of the given problem using the MECE principle.

        Args:
            problem (str): A description of the problem to analyze.

        Returns:
            response (str): A JSON string containing the structured analysis.
        """
        self.notify("Performing structured analysis")
        self.log_tool_call("structured_analysis", {"problem": problem})
        return self._ask_ai(create_analysis_prompt("structured", p=problem))

    @tool
    def analyze_request(self, statement: str) -> str:
        """
        When a request is unclear, high-level or ambiguous use this tool to
        analyze the response and provide a well thought out response.

        Args:
            statement (str): description of problem or errors seen.

        Returns:
            response (str): A well thought out response to the statement or question.
        """
        self.notifier.status("analyzing request...")
        self.log_tool_call("analyze_request", {"statement": statement})
        return self._ask_ai(
            create_analysis_prompt("request", s=statement),
            include_history=True,
            system=self.system_prompt()
        )

    @tool
    def consider_solutions(self, statement: str) -> str:
        """
        Provide a well thought out response to the statement summarize the
        problem and provide a solution or a set of solutions.

        Args:
            statement (str): description of problem or errors seen.

        Returns:
            response (str): A well thought out response to the statement or question.
        """
        self.notifier.status("considering solutions...")
        self.log_tool_call("consider_solutions", {"statement": statement})
        return self._ask_ai(
            create_analysis_prompt("solutions", s=statement),
            include_history=True
        )

    @tool
    def stakeholder_analysis(self, problem_statement: str) -> str:
        """
        Identify and analyze key stakeholders related to the given problem.

        Args:
            problem_statement (str): A description of the problem or situation.

        Returns:
            response (str): A JSON string containing a list of stakeholders, their interests, and potential impacts.
        """
        self.notifier.status("Analyzing stakeholders...")
        return self._ask_ai(
            create_analysis_prompt("stakeholder", p=problem_statement),
            include_history=True
        )

    @tool
    def generate_future_scenarios(self, problem_statement: str, time_horizon: str) -> str:
        """
        Generate potential future scenarios based on the given problem statement and time horizon.

        Args:
            problem_statement (str): A description of the current problem or situation.
            time_horizon (str): The future time frame to consider (e.g., "5 years", "10 years", "50 years").

        Returns:
            response (str): A JSON string containing a list of potential future scenarios.
        """
        self.notifier.status("Generating future scenarios...")
        return self._ask_ai(
            create_analysis_prompt("future_scenarios", p=problem_statement, t=time_horizon)
        )

    @tool
    def system_mapping(self, problem_statement: str) -> str:
        """
        Create a high-level system map based on the given problem statement.

        Args:
            problem_statement (str): A description of the problem or situation.

        Returns:
            response (str): A JSON string representing a high-level system map.
        """
        self.notifier.status("Creating system map...")
        return self._ask_ai(create_analysis_prompt("system_mapping", p=problem_statement))

    @tool
    def risk_assessment(self, problem_statement: str, proposed_solution: str) -> str:
        """
        Perform a risk assessment for the given problem and proposed solution.

        Args:
            problem_statement (str): A description of the problem or situation.
            proposed_solution (str): A description of the proposed solution.

        Returns:
            response (str): A JSON string containing a list of potential risks and their assessments.
        """
        self.notifier.status("Performing risk assessment...")
        return self._ask_ai(
            create_analysis_prompt("risk", p=problem_statement, s=proposed_solution)
        )

    @tool
    def ethical_analysis(self, problem_statement: str, proposed_solution: str) -> str:
        """
        Perform an ethical analysis of the given problem and proposed solution.

        Args:
            problem_statement (str): A description of the problem or situation.
            proposed_solution (str): A description of the proposed solution.

        Returns:
            response (str): A JSON string containing an ethical analysis of the problem and solution.
        """
        self.notifier.status("Performing ethical analysis...")
        return self._ask_ai(
            create_analysis_prompt("ethical", p=problem_statement, s=proposed_solution)
        )