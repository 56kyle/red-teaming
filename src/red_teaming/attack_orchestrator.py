"""
Main test orchestrator for running automated red teaming campaigns.
This is the entry point for executing attacks against Atlas.
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from tqdm import tqdm

from openai_api_target import AtlasTarget
from custom_strategies import AVAILABLE_STRATEGIES, AttackCategory
from scoring_rules import CompositeScorer, ScoringResult, SeverityLevel
from config import Config


# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class AttackResult:
    """Result of a single attack attempt."""
    timestamp: str
    strategy_name: str
    category: str
    prompt: str
    response: str
    scoring_results: Dict[str, Any]
    overall_success: bool
    severity: str
    conversation_turns: int


class AttackOrchestrator:
    """
    Orchestrates automated red teaming campaigns against Atlas.
    
    This class manages the execution of multiple attack strategies,
    collects results, and generates reports.
    """
    
    def __init__(
        self,
        strategies: Optional[List[str]] = None,
        max_prompts_per_strategy: Optional[int] = None,
    ):
        """
        Initialize the attack orchestrator.
        
        Args:
            strategies: List of strategy names to run (None = all)
            max_prompts_per_strategy: Limit prompts per strategy (None = all)
        """
        self.target = AtlasTarget()
        self.scorer = CompositeScorer()
        self.results: List[AttackResult] = []
        
        # Filter strategies if specified
        if strategies:
            self.strategies = [
                s for s in AVAILABLE_STRATEGIES
                if s.name in strategies
            ]
        else:
            self.strategies = AVAILABLE_STRATEGIES
        
        self.max_prompts_per_strategy = max_prompts_per_strategy
        
        logger.info(f"Initialized orchestrator with {len(self.strategies)} strategies")
    
    async def run_campaign(self) -> Dict[str, Any]:
        """
        Run a complete red teaming campaign.
        
        Returns:
            Summary statistics of the campaign
        """
        logger.info("Starting red teaming campaign")
        start_time = datetime.now()
        
        # Collect all prompts to run
        total_prompts = 0
        for strategy in self.strategies:
            prompts = strategy.get_prompts()
            if self.max_prompts_per_strategy:
                prompts = prompts[:self.max_prompts_per_strategy]
            total_prompts += len(prompts)
        
        logger.info(f"Total prompts to test: {total_prompts}")
        
        # Run attacks with progress bar
        with tqdm(total=total_prompts, desc="Running attacks") as pbar:
            for strategy in self.strategies:
                await self._run_strategy(strategy, pbar)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = self._generate_summary(duration)
        
        # Save results
        self._save_results(start_time)
        
        logger.info(f"Campaign completed in {duration:.2f} seconds")
        logger.info(f"Successful attacks: {summary['successful_attacks']}/{summary['total_attacks']}")
        
        return summary
    
    async def _run_strategy(self, strategy, pbar) -> None:
        """Run all prompts for a single strategy."""
        logger.info(f"Testing strategy: {strategy.name}")
        
        prompts = strategy.get_prompts()
        if self.max_prompts_per_strategy:
            prompts = prompts[:self.max_prompts_per_strategy]
        
        for prompt in prompts:
            # Reset conversation for each new prompt
            self.target.reset_conversation()
            
            try:
                result = await self._execute_attack(strategy, prompt)
                self.results.append(result)
                
                # Log if attack was successful
                if result.overall_success:
                    logger.warning(
                        f"SUCCESSFUL ATTACK - Strategy: {strategy.name}, "
                        f"Severity: {result.severity}"
                    )
                
            except Exception as e:
                logger.error(f"Error executing attack: {e}", exc_info=True)
            
            pbar.update(1)
            
            # Small delay between prompts
            await asyncio.sleep(0.1)
    
    async def _execute_attack(self, strategy, prompt: str) -> AttackResult:
        """Execute a single attack and score the result."""
        from pyrit.models import PromptRequestResponse, PromptRequestPiece
        
        # Create prompt request
        request_piece = PromptRequestPiece(
            role="user",
            original_value=prompt,
            converted_value=prompt,
            original_value_data_type="text",
            converted_value_data_type="text",
        )
        
        request = PromptRequestResponse(request_pieces=[request_piece])
        
        # Send to Atlas
        response = await self.target.send_prompt_async(request)
        
        # Extract response text
        response_text = response.request_pieces[-1].converted_value
        
        # Score the response
        scoring_results = self.scorer.score_all(prompt, response_text)
        worst_result = self.scorer.get_worst_result(scoring_results)
        
        # Create attack result
        return AttackResult(
            timestamp=datetime.now().isoformat(),
            strategy_name=strategy.name,
            category=strategy.category.value,
            prompt=prompt,
            response=response_text,
            scoring_results={
                name: {
                    "is_successful": result.is_successful,
                    "severity": result.severity.value,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "score": result.score,
                }
                for name, result in scoring_results.items()
            },
            overall_success=worst_result.is_successful,
            severity=worst_result.severity.value,
            conversation_turns=self.target.get_conversation_length(),
        )
    
    def _generate_summary(self, duration: float) -> Dict[str, Any]:
        """Generate summary statistics from results."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.overall_success)
        
        # Count by severity
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
        results_file = Config.RESULTS_DIR / f"results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(
                [asdict(r) for r in self.results],
                f,
                indent=2
            )
        
        logger.info(f"Results saved to {results_file}")
        
        # Save successful attacks separately for easy review
        successful = [r for r in self.results if r.overall_success]
        if successful:
            success_file = Config.RESULTS_DIR / f"successful_{timestamp}.json"
            with open(success_file, 'w') as f:
                json.dump(
                    [asdict(r) for r in successful],
                    f,
                    indent=2
                )
            logger.info(f"Successful attacks saved to {success_file}")


async def main():
    """Main entry point for the attack orchestrator."""
    print("=" * 80)
    print("Atlas Red Teaming Harness")
    print("=" * 80)
    print(Config.get_summary())
    print("=" * 80)
    
    # Create orchestrator
    orchestrator = AttackOrchestrator()
    
    # Run campaign
    summary = await orchestrator.run_campaign()
    
    # Print summary
    print("\n" + "=" * 80)
    print("Campaign Summary")
    print("=" * 80)
    print(f"Total Attacks: {summary['total_attacks']}")
    print(f"Successful Attacks: {summary['successful_attacks']}")
    print(f"Success Rate: {summary['success_rate']:.2%}")
    print(f"Duration: {summary['duration_seconds']:.2f} seconds")
    print(f"\nSeverity Breakdown:")
    for severity, count in summary['severity_breakdown'].items():
        if count > 0:
            print(f"  {severity.upper()}: {count}")
    print(f"\nCategory Success Rates:")
    for category, rate in summary['category_success_rates'].items():
        print(f"  {category}: {rate:.2%}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

