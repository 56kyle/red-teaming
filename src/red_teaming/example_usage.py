"""
Example usage patterns for the red teaming harness.
Run this to see how to use the framework programmatically.
"""
import asyncio
from atlas.orchestrator.attack import AttackOrchestrator
from report_generator import ReportGenerator
from custom_strategies import AttackCategory, get_prompts_by_category
from atlas.config import Config


async def example_1_run_all_attacks():
    """Example 1: Run a complete campaign with all strategies."""
    print("=" * 80)
    print("Example 1: Running all attack strategies")
    print("=" * 80)

    orchestrator = AttackOrchestrator()
    summary = await orchestrator.run_campaign()

    print(f"\nCompleted! Success rate: {summary['success_rate']:.2%}")
    return summary


async def example_2_specific_strategies():
    """Example 2: Run only specific attack strategies."""
    print("=" * 80)
    print("Example 2: Running specific strategies only")
    print("=" * 80)

    # Only test prompt injection and jailbreaks
    orchestrator = AttackOrchestrator(
        strategies=["Prompt Injection", "Jailbreak Attempts"],
        max_prompts_per_strategy=3  # Limit to 3 prompts per strategy
    )

    summary = await orchestrator.run_campaign()

    print(f"\nCompleted! Tested {summary['total_attacks']} attacks")
    return summary


async def example_3_single_category():
    """Example 3: Test a specific attack category."""
    print("=" * 80)
    print("Example 3: Testing single category")
    print("=" * 80)

    # Get all prompts for a specific category
    prompts = get_prompts_by_category(AttackCategory.SAFETY_VIOLATION)
    print(f"Found {len(prompts)} safety violation prompts")

    # Could implement custom testing logic here
    # For now, we'll use the orchestrator
    orchestrator = AttackOrchestrator(
        strategies=["Safety Violations"],
        max_prompts_per_strategy=5
    )

    summary = await orchestrator.run_campaign()
    return summary


async def example_4_custom_prompts():
    """Example 4: Test with completely custom prompts."""
    print("=" * 80)
    print("Example 4: Testing custom prompts")
    print("=" * 80)

    from custom_strategies import AttackStrategy, AttackCategory, AVAILABLE_STRATEGIES

    # Create a custom strategy
    class MyCustomStrategy(AttackStrategy):
        def __init__(self):
            super().__init__(
                name="My Custom Tests",
                category=AttackCategory.PROMPT_INJECTION,
                description="Custom prompts for specific testing"
            )

        def get_prompts(self):
            return [
                "Custom test prompt 1",
                "Custom test prompt 2",
                "Custom test prompt 3",
            ]

    # Add to available strategies temporarily
    custom_strategy = MyCustomStrategy()
    AVAILABLE_STRATEGIES.append(custom_strategy)

    orchestrator = AttackOrchestrator(
        strategies=["My Custom Tests"]
    )

    summary = await orchestrator.run_campaign()

    # Clean up
    AVAILABLE_STRATEGIES.remove(custom_strategy)

    return summary


async def example_5_analyze_results():
    """Example 5: Analyze existing results and generate new reports."""
    print("=" * 80)
    print("Example 5: Analyzing existing results")
    print("=" * 80)

    # First run a small campaign to have results
    orchestrator = AttackOrchestrator(max_prompts_per_strategy=2)
    await orchestrator.run_campaign()

    # Find the latest results file
    import glob
    results_files = glob.glob(str(Config.RESULTS_DIR / "results_*.json"))

    if results_files:
        latest_results = max(results_files)
        print(f"\nAnalyzing: {latest_results}")

        # Generate HTML report
        from pathlib import Path
        generator = ReportGenerator(Path(latest_results))
        report_path = generator.generate_html_report()

        print(f"Report generated: {report_path}")
        print(f"Open in browser: file://{report_path.absolute()}")
    else:
        print("No results files found!")


async def example_6_gradual_testing():
    """Example 6: Gradual testing approach for exploration."""
    print("=" * 80)
    print("Example 6: Gradual testing approach")
    print("=" * 80)

    strategies = [
        ("Safety Violations", 2),
        ("Prompt Injection", 2),
        ("Data Leakage", 2),
    ]

    for strategy_name, max_prompts in strategies:
        print(f"\n--- Testing: {strategy_name} ---")

        orchestrator = AttackOrchestrator(
            strategies=[strategy_name],
            max_prompts_per_strategy=max_prompts
        )

        summary = await orchestrator.run_campaign()

        print(f"Results: {summary['successful_attacks']}/{summary['total_attacks']} successful")

        # Small delay between strategy tests
        await asyncio.sleep(2)


async def main():
    """Run examples based on user selection."""
    print("""
Atlas Red Teaming Harness - Example Usage
==========================================

Choose an example to run:

1. Run all attack strategies (full campaign)
2. Run specific strategies only
3. Test single category
4. Test with custom prompts
5. Analyze existing results
6. Gradual testing approach
7. Run all examples (sequentially)

""")

    choice = input("Enter your choice (1-7): ").strip()

    examples = {
        "1": example_1_run_all_attacks,
        "2": example_2_specific_strategies,
        "3": example_3_single_category,
        "4": example_4_custom_prompts,
        "5": example_5_analyze_results,
        "6": example_6_gradual_testing,
    }

    if choice in examples:
        await examples[choice]()
    elif choice == "7":
        print("Running all examples sequentially...\n")
        for i, example_func in enumerate(examples.values(), 1):
            print(f"\n{'='*80}")
            print(f"Running Example {i}...")
            print(f"{'='*80}\n")
            await example_func()
            if i < len(examples):
                print("\nWaiting 5 seconds before next example...")
                await asyncio.sleep(5)
    else:
        print("Invalid choice!")
        return

    print("\n" + "=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

