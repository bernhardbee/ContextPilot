"""
Simple functional test for backend without model loading.
"""
from models import ContextUnit, ContextType
from storage import context_store
from composer import prompt_composer


def test_basic_functionality():
    """Test basic functionality without model."""
    print("🧪 Testing ContextPilot Basic Functionality")
    print("=" * 50)
    
    # Test 1: Create contexts
    print("\n1. Creating contexts...")
    context1 = ContextUnit(
        type=ContextType.PREFERENCE,
        content="I prefer Python for backend development",
        confidence=0.95,
        tags=["python", "backend"]
    )
    
    context2 = ContextUnit(
        type=ContextType.DECISION,
        content="Using FastAPI for REST APIs",
        confidence=0.9,
        tags=["fastapi", "api"]
    )
    
    context_store.add(context1)
    context_store.add(context2)
    print(f"   ✓ Created {len(context_store.list_all())} contexts")
    
    # Test 2: List contexts
    print("\n2. Listing contexts...")
    contexts = context_store.list_all()
    for ctx in contexts:
        print(f"   - [{ctx.type.value}] {ctx.content[:50]}...")
    
    # Test 3: Update context
    print("\n3. Updating context...")
    updates = {"confidence": 0.98}
    updated = context_store.update(context1.id, updates)
    print(f"   ✓ Updated confidence to {updated.confidence}")
    
    # Test 4: Test prompt composer (without relevance engine)
    print("\n4. Testing prompt composer...")
    from models import RankedContextUnit
    
    ranked = [
        RankedContextUnit(context_unit=context1, relevance_score=0.85),
        RankedContextUnit(context_unit=context2, relevance_score=0.80)
    ]
    
    task = "Create a new API endpoint for user management"
    prompt = prompt_composer.compose(task, ranked)
    
    print(f"   ✓ Generated prompt ({len(prompt.generated_prompt)} chars)")
    print(f"\n   Preview:")
    print("   " + "─" * 47)
    for line in prompt.generated_prompt.split('\n')[:10]:
        print(f"   {line}")
    print("   ...")
    
    # Test 5: Test supersede
    print("\n5. Testing context superseding...")
    new_context = ContextUnit(
        type=ContextType.PREFERENCE,
        content="I prefer Python 3.11+ for backend development",
        confidence=0.95,
        tags=["python", "backend"]
    )
    context_store.supersede(context1.id, new_context)
    
    active_contexts = context_store.list_all(include_superseded=False)
    all_contexts = context_store.list_all(include_superseded=True)
    print(f"   ✓ Active: {len(active_contexts)}, Total: {len(all_contexts)}")
    
    # Test 6: Delete context
    print("\n6. Testing context deletion...")
    success = context_store.delete(context2.id)
    print(f"   ✓ Deleted: {success}")
    
    print("\n" + "=" * 50)
    print("✅ All functional tests passed!")
    print("")


if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
