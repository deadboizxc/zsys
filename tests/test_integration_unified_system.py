"""
Integration Test: Verify all unified systems work together

This tests:
1. Models can be imported from zsys.models
2. Schemas can be imported from zsys.data.schemas
3. ORM can be imported from zsys.core.base.models
4. qp-media schemas use unified schemas
5. monet database uses unified ORM
"""

import sys
from pathlib import Path

# Add workspace to path
workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))


def test_imports_unified_core():
    """Test importing unified core components."""
    print("\n[1] Testing unified core imports...")
    
    from zsys.core.base.models import (
        Base,
        BaseModel,
        BaseSchema,
        DatabaseSession,
        ORMConfig,
        init_db,
        get_db,
    )
    
    assert Base is not None
    assert BaseModel is not None
    assert BaseSchema is not None
    assert DatabaseSession is not None
    assert ORMConfig is not None
    assert init_db is not None
    assert get_db is not None
    
    print("   ✅ All core components imported successfully")


def test_imports_unified_models():
    """Test importing unified models."""
    print("\n[2] Testing unified models imports...")
    
    from zsys.data.orm import User, Chat, Message, MediaFile, Wallet
    
    assert User is not None
    assert Chat is not None
    assert Message is not None
    assert MediaFile is not None
    assert Wallet is not None
    
    # Check they have required columns
    assert hasattr(User, 'id')
    assert hasattr(User, 'username')
    assert hasattr(Chat, 'title')
    assert hasattr(Message, 'text')
    assert hasattr(MediaFile, 'filename')
    assert hasattr(Wallet, 'address')
    
    print("   ✅ All unified models imported successfully")


def test_imports_unified_schemas():
    """Test importing unified schemas."""
    print("\n[3] Testing unified schemas imports...")
    
    from zsys.data.schemas import (
        UserResponse,
        ChatResponse,
        MessageResponse,
        MediaResponse,
        WalletResponse,
        ErrorResponse,
        TokenRequest,
        TokenResponse,
        PaginationMeta,
        MediaListResponse,
    )
    
    assert UserResponse is not None
    assert ChatResponse is not None
    assert MessageResponse is not None
    assert MediaResponse is not None
    assert WalletResponse is not None
    assert ErrorResponse is not None
    assert TokenRequest is not None
    assert TokenResponse is not None
    assert PaginationMeta is not None
    assert MediaListResponse is not None
    
    print("   ✅ All unified schemas imported successfully")


def test_qpmedia_schema_integration():
    """Test qp-media is using unified schemas."""
    print("\n[4] Testing qp-media schema integration...")
    
    sys.path.insert(0, str(workspace / "qp-media"))
    from api.rest.schemas import (
        ErrorResponse,
        TokenRequest,
        TokenResponse,
        PaginationMeta,
    )
    
    # These should be imported from zsys.data.schemas (unified)
    from zsys.data.schemas import (
        ErrorResponse as UnifiedErrorResponse,
        TokenRequest as UnifiedTokenRequest,
        TokenResponse as UnifiedTokenResponse,
        PaginationMeta as UnifiedPaginationMeta,
    )
    
    # Verify shared schemas are unified
    assert ErrorResponse is UnifiedErrorResponse, "qp-media should use unified ErrorResponse"
    assert TokenRequest is UnifiedTokenRequest, "qp-media should use unified TokenRequest"
    assert TokenResponse is UnifiedTokenResponse, "qp-media should use unified TokenResponse"
    assert PaginationMeta is UnifiedPaginationMeta, "qp-media should use unified PaginationMeta"
    
    # MediaListResponse and MediaResponse can be project-specific
    # because they use project-specific MediaResponse structure
    
    print("   ✅ qp-media is correctly using unified shared schemas")


def test_monet_orm_integration():
    """Test monet is using unified ORM."""
    print("\n[5] Testing monet ORM integration...")
    
    sys.path.insert(0, str(workspace / "monet"))
    from database import (
        Base,
        db_session,
        get_db_session,
    )
    
    # These should be from unified system
    from zsys.core.base.models import (
        Base as UnifiedBase,
        init_db,
    )
    
    # Verify they're using unified components
    assert Base is UnifiedBase, "monet should use unified Base"
    assert db_session is not None, "monet should have db_session instance"
    
    print("   ✅ monet is correctly using unified ORM")


def test_orm_functionality():
    """Test that ORM actually works."""
    print("\n[6] Testing ORM functionality...")
    
    from zsys.core.base.models import init_db, ORMConfig
    from zsys.data.orm import User
    
    # Create in-memory SQLite for testing
    config = ORMConfig("sqlite:///:memory:")
    db = init_db(config)
    db.create_all()
    
    # Test creating a record
    with db.get_session() as session:
        user = User(username="test", email="test@example.com")
        session.add(user)
        session.flush()
        
        # Query it back
        found = session.query(User).filter(User.username == "test").first()
        assert found is not None, "User should be found in database"
        assert found.username == "test"
        assert found.created_at is not None
    
    print("   ✅ ORM functionality works correctly")


def test_schema_validation():
    """Test that schema validation works."""
    print("\n[7] Testing schema validation...")
    
    from zsys.data.schemas import UserResponse, UserCreate
    from datetime import datetime
    
    # Create instance
    user_create = UserCreate(
        username="john",
        email="john@example.com",
        first_name="John",
        last_name="Doe"
    )
    
    assert user_create.username == "john"
    assert user_create.email == "john@example.com"
    
    # Create response
    user_response = UserResponse(
        id=1,
        username="john",
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        is_bot=False,
        is_premium=False,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        language_code="en"
    )
    
    assert user_response.id == 1
    assert user_response.email == "john@example.com"
    
    print("   ✅ Schema validation works correctly")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 70)
    print("UNIFIED ARCHITECTURE INTEGRATION TESTS")
    print("=" * 70)
    
    try:
        test_imports_unified_core()
        test_imports_unified_models()
        test_imports_unified_schemas()
        test_qpmedia_schema_integration()
        test_monet_orm_integration()
        test_orm_functionality()
        test_schema_validation()
        
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 70)
        print("\n📊 Summary:")
        print("   ✅ Unified core components working")
        print("   ✅ Unified models working")
        print("   ✅ Unified schemas working")
        print("   ✅ qp-media integrated with unified schemas")
        print("   ✅ monet integrated with unified ORM")
        print("   ✅ ORM functionality verified")
        print("   ✅ Schema validation working")
        print("\n🎉 Unified architecture is fully functional!\n")
        
        return True
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
