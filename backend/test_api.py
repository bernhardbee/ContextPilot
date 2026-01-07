"""
Test script for ContextPilot API.
"""
import asyncio
from models import ContextType
from storage import context_store
from relevance import relevance_engine
from composer import prompt_composer
from example_data import load_example_data


async def test_contextpilot():
    """Run tests for ContextPilot."""
    print("🧭 Testing ContextPilot")
    print("=" * 50)
    
    # Load example data
    print("\n1. Loading example data...")
    count = load_example_data()
    print(f"   ✓ Loaded {count} contexts")
    
    # List contexts
    print("\n2. Listing contexts...")
    contexts = context_store.list_all()
    print(f"   ✓ Found {len(contexts)} active contexts")
    
    for ctx in contexts[:3]:
        print(f"   - [{ctx.type.value}] {ctx.content[:50]}...")
    
    # Test relevance engine
    print("\n3. Testing relevance engine...")
    task1 = "Write a Python function to calculate fibonacci numbers"
    ranked1 = relevance_engine.rank_with_keywords(task1, context_store, max_results=3)
    print(f"   Task: {task1}")
    print(f"   ✓ Found {len(ranked1)} relevant contexts:")
    for ranked in ranked1:
        print(f"   - Score: {ranked.relevance_score:.3f} | {ranked.context_unit.content[:60]}...")
    
    # Test prompt composer
    print("\n4. Testing prompt composer...")
    generated = prompt_composer.compose(task1, ranked1)
    print(f"   ✓ Generated prompt ({len(generated.generated_prompt)} chars)")
    print("\n" + "=" * 50)
    print(generated.generated_prompt)
    print("=" * 50)
    
    # Test another task
    print("\n5. Testing another task...")
    task2 = "Design a React component for displaying user preferences"
    ranked2 = relevance_engine.rank_with_keywords(task2, context_store, max_results=5)
    print(f"   Task: {task2}")
    print(f"   ✓ Found {len(ranked2)} relevant contexts:")
    for ranked in ranked2:
        print(f"   - Score: {ranked.relevance_score:.3f} | {ranked.context_unit.content[:60]}...")
    
    generated2 = prompt_composer.compose_compact(task2, ranked2)
    print(f"   ✓ Generated compact prompt ({len(generated2.generated_prompt)} chars)")
    print("\n" + "=" * 50)
    print(generated2.generated_prompt)
    print("=" * 50)
    
    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_contextpilot())
