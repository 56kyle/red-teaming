"""Module containing logic defining out the pyrit orchestrator that will be used throughout the atlas package."""
import asyncio
import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from tqdm import tqdm

from atlas.prompt_target.browser import AtlasBrowserTarget
from atlas.score.composite import AtlasCompositeScorer
from red_teaming.atlas_attack_strategies import ATLAS_ATTACK_SCENARIOS
from red_teaming.atlas_attack_strategies import BrowserAttackScenario
from atlas.orchestrator.attack import logger
from red_teaming.config import Config
from red_teaming.test_server import TestServer


@dataclass
class AtlasAttackResult:
    """Result of an Atlas browser attack."""
    timestamp: str
    scenario_name: str
    category: str
    test_page: str
    page_url: str
    prompts_sent: List[str]
    ai_responses: List[str]
    scoring_results: Dict[str, Any]
    overall_success: bool
    severity: str
    screenshots: List[str]
    success_indicators_found: List[str]


class AtlasOrchestrator:
    """
    Orchestrates browser-based red teaming campaigns against Atlas.

    Manages:
    - Test server for hosting adversarial pages
    - Browser automation
    - Attack scenario execution
    - AI response scoring
    - Result collection and reporting
    """

    def __init__(
        self,
        scenarios: Optional[List[str]] = None,
        headless: bool = None,
    ):
        """
        Initialize the Atlas orchestrator.

        Args:
            scenarios: List of scenario names to run (None = all)
            headless: Run browser in headless mode (None = use config)
        """
        self.browser = AtlasBrowserTarget(
            headless=headless if headless is not None else Config.HEADLESS_MODE,
            slow_mo=Config.BROWSER_SLOW_MO,
            screenshot_on_interaction=Config.SCREENSHOT_ON_INTERACTION,
        )

        self.scorer = AtlasCompositeScorer()
        self.server = TestServer(
            host=Config.TEST_SERVER_HOST,
            port=Config.TEST_SERVER_PORT,
        )

        self.results: List[AtlasAttackResult] = []

        # Filter scenarios if specified
        if scenarios:
            self.scenarios = [
                s for s in ATLAS_ATTACK_SCENARIOS
                if s.name in scenarios
            ]
        else:
            self.scenarios = ATLAS_ATTACK_SCENARIOS

        from atlas.orchestrator.attack import logger
        logger.info(f"Initialized orchestrator with {len(self.scenarios)} scenarios")

    async def run_campaign(self) -> Dict[str, Any]:
        """
        Run a complete browser-based red teaming campaign.

        Returns:
            Summary statistics of the campaign
        """
        logger.info("Starting Atlas browser red teaming campaign")
        start_time = datetime.now()

        try:
            # Start test server
            self.server.start()
            logger.info(f"Test server running at {self.server.get_url()}")

            # Launch browser
            await self.browser.launch()
            logger.info("Atlas browser launched")

            # Run attack scenarios with progress bar
            with tqdm(total=len(self.scenarios), desc="Running attack scenarios") as pbar:
                for scenario in self.scenarios:
                    try:
                        result = await self._run_scenario(scenario)
                        self.results.append(result)

                        if result.overall_success:
                            logger.warning(
                                f"🚨 SUCCESSFUL ATTACK - Scenario: {scenario.name}, "
                                f"Severity: {result.severity}"
                            )

                        # Delay between tests
                        await asyncio.sleep(Config.DELAY_BETWEEN_TESTS)

                    except Exception as e:
                        logger.error(f"Error in scenario '{scenario.name}': {e}", exc_info=True)

                    pbar.update(1)

        finally:
            # Cleanup
            await self.browser.close()
            self.server.stop()
            logger.info("Browser closed and server stopped")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Generate summary
        summary = self._generate_summary(duration)

        # Save results
        self._save_results(start_time)

        logger.info(f"Campaign completed in {duration:.2f} seconds")
        logger.info(f"Successful attacks: {summary['successful_attacks']}/{summary['total_attacks']}")

        return summary

    async def _run_scenario(self, scenario: BrowserAttackScenario) -> AtlasAttackResult:
        """Execute a single attack scenario."""
        logger.info(f"Testing scenario: {scenario.name}")

        # Navigate to test page
        page_url = self.server.get_url(scenario.test_page.replace('.html', ''))
        await self.browser.navigate(page_url)

        # Wait for page to load
        await asyncio.sleep(2)

        # Send prompts and collect responses
        ai_responses = []
        for prompt in scenario.interaction_prompts:
            logger.info(f"Sending prompt: {prompt[:50]}...")
            response = await self.browser.interact_with_sidebar(prompt)

            if response:
                ai_responses.append(response)
                logger.info(f"Got response: {response[:100]}...")
            else:
                ai_responses.append("[No response received]")
                logger.warning("No response received from AI")

            await asyncio.sleep(1)

        # Score the responses
        scoring_results = {}
        success_indicators_found = []

        for i, (prompt, response) in enumerate(zip(scenario.interaction_prompts, ai_responses)):
            scores = self.scorer.score_all(prompt, response)
            scoring_results[f"interaction_{i+1}"] = {
                name: {
                    "is_successful": result.is_successful,
                    "severity": result.severity.value,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "score": result.score,
                }
                for name, result in scores.items()
            }

            # Check for success indicators
            response_lower = response.lower()
            for indicator in scenario.success_indicators:
                if indicator.lower() in response_lower:
                    success_indicators_found.append(indicator)

        # Determine overall success
        worst_result = None
        worst_score = 0
        for interaction_scores in scoring_results.values():
            for score_data in interaction_scores.values():
                if score_data['score'] > worst_score:
                    worst_score = score_data['score']
                    worst_result = score_data

        overall_success = worst_result and worst_result['is_successful'] if worst_result else False
        severity = worst_result['severity'] if worst_result else 'none'

        # Also mark as successful if we found specific success indicators
        if success_indicators_found:
            overall_success = True
            if severity == 'none':
                severity = 'high'

        # Collect screenshots
        screenshots = [
            str(interaction.screenshot_path)
            for interaction in self.browser.get_interactions()
            if interaction.screenshot_path
        ]

        return AtlasAttackResult(
            timestamp=datetime.now().isoformat(),
            scenario_name=scenario.name,
            category=scenario.category.value,
            test_page=scenario.test_page,
            page_url=page_url,
            prompts_sent=scenario.interaction_prompts,
            ai_responses=ai_responses,
            scoring_results=scoring_results,
            overall_success=overall_success,
            severity=severity,
            screenshots=screenshots,
            success_indicators_found=success_indicators_found,
        )

    def _generate_summary(self, duration: float) -> Dict[str, Any]:
        """Generate summary statistics from results."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.overall_success)

        # Count by severity
        from scoring_rules import SeverityLevel
        severity_counts = {level.value: 0 for level in SeverityLevel}
        for result in self.results:
            severity_counts[result.severity] += 1

        # Count by category
        category_counts = {}
        category_success = {}
        for result in self.results:
            cat = result.category
            category_counts[cat] = category_counts.get(cat, 0) + 1
            if result.overall_success:
                category_success[cat] = category_success.get(cat, 0) + 1

        return {
            "total_attacks": total,
            "successful_attacks": successful,
            "success_rate": successful / total if total > 0 else 0,
            "duration_seconds": duration,
            "attacks_per_second": total / duration if duration > 0 else 0,
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "category_success_rates": {
                cat: category_success.get(cat, 0) / count
                for cat, count in category_counts.items()
            }
        }

    def _save_results(self, start_time: datetime) -> None:
        """Save results to disk."""
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")

        # Save detailed results as JSON
        results_file = Config.RESULTS_DIR / f"atlas_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(
                [asdict(r) for r in self.results],
                f,
                indent=2
            )

        logger.info(f"Results saved to {results_file}")

        # Save successful attacks separately
        successful = [r for r in self.results if r.overall_success]
        if successful:
            success_file = Config.RESULTS_DIR / f"atlas_successful_{timestamp}.json"
            with open(success_file, 'w') as f:
                json.dump(
                    [asdict(r) for r in successful],
                    f,
                    indent=2
                )
            logger.info(f"Successful attacks saved to {success_file}")
