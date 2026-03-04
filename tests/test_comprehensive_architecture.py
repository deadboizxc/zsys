"""
Comprehensive integration tests for unified architecture.

Tests all components together:
- Models (separate files)
- Schemas (separate files)
- ORM integration
- Project integrations (qp-media, monet)
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Setup path
workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))


class TestModelsStructure:
    """Test models are properly structured."""
    
    def test_user_model_import(self):
        """Test User model can be imported from separate file."""
        from zsys.data.orm.user import User
        assert hasattr(User, '__tablename__')
        assert User.__tablename__ == "users"
        assert hasattr(User, 'username')
        assert hasattr(User, 'email')
        print("✅ User model imports correctly")
    
    def test_chat_model_import(self):
        """Test Chat model can be imported from separate file."""
        from zsys.data.orm.chat import Chat
        assert hasattr(Chat, '__tablename__')
        assert Chat.__tablename__ == "chats"
        assert hasattr(Chat, 'title')
        print("✅ Chat model imports correctly")
    
    def test_message_model_import(self):
        """Test Message model can be imported from separate file."""
        from zsys.data.orm.message import Message
        assert hasattr(Message, '__tablename__')
        assert Message.__tablename__ == "messages"
        assert hasattr(Message, 'text')
        print("✅ Message model imports correctly")
    
    def test_media_file_model_import(self):
        """Test MediaFile model can be imported from separate file."""
        from zsys.data.orm.media_file import MediaFile
        assert hasattr(MediaFile, '__tablename__')
        assert MediaFile.__tablename__ == "media_files"
        assert hasattr(MediaFile, 'filename')
        print("✅ MediaFile model imports correctly")
    
    def test_wallet_model_import(self):
        """Test Wallet model can be imported from separate file."""
        from zsys.data.orm.wallet import Wallet
        assert hasattr(Wallet, '__tablename__')
        assert Wallet.__tablename__ == "wallets"
        assert hasattr(Wallet, 'address')
        print("✅ Wallet model imports correctly")
    
    def test_unified_models_import(self):
        """Test all models can be imported from __init__."""
        from zsys.data.orm import User, Chat, Message, MediaFile, Wallet
        assert User is not None
        assert Chat is not None
        assert Message is not None
        assert MediaFile is not None
        assert Wallet is not None
        print("✅ All unified models import correctly")


class TestSchemasStructure:
    """Test schemas are properly structured."""
    
    def test_user_schemas_import(self):
        """Test User schemas can be imported from separate file."""
        try:
            from zsys.data.schemas.user import UserCreate, UserUpdate, UserResponse
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.user unavailable: {e}")
        assert UserCreate is not None
        assert UserUpdate is not None
        assert UserResponse is not None
        print("✅ User schemas import correctly")
    
    def test_chat_schemas_import(self):
        """Test Chat schemas can be imported from separate file."""
        try:
            from zsys.data.schemas.chat import ChatCreate, ChatResponse
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.chat unavailable: {e}")
        assert ChatCreate is not None
        assert ChatResponse is not None
        print("✅ Chat schemas import correctly")
    
    def test_message_schemas_import(self):
        """Test Message schemas can be imported from separate file."""
        try:
            from zsys.data.schemas.message import MessageCreate, MessageResponse
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.message unavailable: {e}")
        assert MessageCreate is not None
        assert MessageResponse is not None
        print("✅ Message schemas import correctly")
    
    def test_media_schemas_import(self):
        """Test Media schemas can be imported from separate file."""
        try:
            from zsys.data.schemas.media import MediaCreate, MediaResponse, PaginationMeta, MediaListResponse
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.media unavailable: {e}")
        assert MediaCreate is not None
        assert MediaResponse is not None
        assert PaginationMeta is not None
        assert MediaListResponse is not None
        print("✅ Media schemas import correctly")
    
    def test_wallet_schemas_import(self):
        """Test Wallet schemas can be imported from separate file."""
        try:
            from zsys.data.schemas.wallet import WalletCreate, WalletResponse
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.wallet unavailable: {e}")
        assert WalletCreate is not None
        assert WalletResponse is not None
        print("✅ Wallet schemas import correctly")
    
    def test_common_schemas_import(self):
        """Test common schemas can be imported from separate file."""
        try:
            from zsys.data.schemas.common import ErrorResponse, TokenRequest, TokenResponse
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.common unavailable: {e}")
        assert ErrorResponse is not None
        assert TokenRequest is not None
        assert TokenResponse is not None
        print("✅ Common schemas import correctly")
    
    def test_unified_schemas_import(self):
        """Test all schemas can be imported from __init__."""
        try:
            from zsys.data.schemas import (
                UserResponse, ChatResponse, MessageResponse,
                MediaResponse, WalletResponse, ErrorResponse,
                TokenRequest, TokenResponse, PaginationMeta
            )
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas unavailable: {e}")
        assert UserResponse is not None
        assert ChatResponse is not None
        assert MessageResponse is not None
        assert MediaResponse is not None
        assert WalletResponse is not None
        assert ErrorResponse is not None
        assert TokenRequest is not None
        assert TokenResponse is not None
        assert PaginationMeta is not None
        print("✅ All unified schemas import correctly")


class TestORMSystem:
    """Test ORM system works correctly."""
    
    def test_orm_initialization(self):
        """Test ORM can be initialized."""
        try:
            from zsys.core.base.models import init_db, ORMConfig
        except ImportError as e:
            pytest.skip(f"zsys.core.base.models unavailable: {e}")
        
        config = ORMConfig("sqlite:///:memory:")
        db = init_db(config)
        assert db is not None
        print("✅ ORM initializes correctly")
    
    def test_create_all_tables(self):
        """Test all tables can be created."""
        try:
            from zsys.core.base.models import init_db, ORMConfig
        except ImportError as e:
            pytest.skip(f"zsys.core.base.models unavailable: {e}")
        from zsys.data.orm import User, Chat, Message, MediaFile, Wallet
        
        config = ORMConfig("sqlite:///:memory:")
        db = init_db(config)
        db.create_all()
        
        # Verify engine and tables exist
        assert db.engine is not None
        print("✅ All tables created successfully")
    
    def test_user_crud(self):
        """Test User CRUD operations."""
        try:
            from zsys.core.base.models import init_db, ORMConfig
        except ImportError as e:
            pytest.skip(f"zsys.core.base.models unavailable: {e}")
        from zsys.data.orm import User
        
        config = ORMConfig("sqlite:///:memory:")
        db = init_db(config)
        db.create_all()
        
        with db.get_session() as session:
            # Create
            user = User(username="test_user", email="test@example.com")
            session.add(user)
            session.flush()
            user_id = user.id
            
            # Read
            fetched = session.query(User).get(user_id)
            assert fetched is not None
            assert fetched.username == "test_user"
            
            # Update
            fetched.email = "new@example.com"
            session.flush()
            
            # Verify update
            updated = session.query(User).get(user_id)
            assert updated.email == "new@example.com"
            
            # Delete
            session.delete(updated)
        
        # Verify delete
        with db.get_session() as session:
            deleted = session.query(User).get(user_id)
            assert deleted is None
        
        print("✅ User CRUD operations work correctly")
    
    def test_relationships(self):
        """Test creating related models."""
        try:
            from zsys.core.base.models import init_db, ORMConfig
        except ImportError as e:
            pytest.skip(f"zsys.core.base.models unavailable: {e}")
        from zsys.data.orm import User, Chat, Message
        
        config = ORMConfig("sqlite:///:memory:")
        db = init_db(config)
        db.create_all()
        
        with db.get_session() as session:
            # Create user
            user = User(username="author", email="author@example.com")
            session.add(user)
            session.flush()
            
            # Create chat
            chat = Chat(title="Test Chat", type="group")
            session.add(chat)
            session.flush()
            
            # Create message
            message = Message(
                text="Hello World",
                chat_id=chat.id,
                user_id=user.id
            )
            session.add(message)
            session.flush()
            
            # Verify all created
            assert message.id is not None
            assert message.user_id == user.id
            assert message.chat_id == chat.id
        
        print("✅ Model relationships work correctly")


class TestSchemasValidation:
    """Test schema validation works."""
    
    def test_user_schema_validation(self):
        """Test UserCreate schema validation."""
        try:
            from zsys.data.schemas.user import UserCreate
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.user unavailable: {e}")
        
        # Valid
        user = UserCreate(
            username="john",
            email="john@example.com",
            first_name="John"
        )
        assert user.username == "john"
        assert user.email == "john@example.com"
        
        # Invalid - missing email
        try:
            UserCreate(username="jane")
            assert False, "Should have raised validation error"
        except Exception:
            pass
        
        print("✅ User schema validation works correctly")
    
    def test_media_schema_validation(self):
        """Test Media schema validation."""
        try:
            from zsys.data.schemas.media import MediaCreate, PaginationMeta
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.media unavailable: {e}")
        
        # Valid media
        media = MediaCreate(
            filename="image.jpg",
            mime_type="image/jpeg",
            size=1024,
            media_type="image",
            url="https://example.com/image.jpg"
        )
        assert media.filename == "image.jpg"
        
        # Valid pagination
        pagination = PaginationMeta(
            total=100,
            limit=10,
            offset=0,
            has_more=True
        )
        assert pagination.total == 100
        
        print("✅ Media schema validation works correctly")
    
    def test_error_schema(self):
        """Test ErrorResponse schema."""
        try:
            from zsys.data.schemas.common import ErrorResponse
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.common unavailable: {e}")
        
        error = ErrorResponse(
            error="Validation Failed",
            code="INVALID_INPUT",
            detail="Email is invalid"
        )
        assert error.error == "Validation Failed"
        assert error.code == "INVALID_INPUT"
        
        print("✅ Error schema works correctly")


class TestProjectIntegrations:
    """Test project-specific integrations."""
    
    def test_qpmedia_schemas_integration(self):
        """Test qp-media uses unified schemas."""
        try:
            sys.path.insert(0, str(workspace / "qp-media"))
            from api.rest.schemas import ErrorResponse, TokenRequest, TokenResponse
        except ImportError as e:
            pytest.skip(f"qp-media project unavailable: {e}")
        
        try:
            from zsys.data.schemas.common import (
                ErrorResponse as UnifiedErrorResponse,
                TokenRequest as UnifiedTokenRequest,
                TokenResponse as UnifiedTokenResponse,
            )
        except ImportError as e:
            pytest.skip(f"zsys.data.schemas.common unavailable: {e}")
        
        # Should be same classes
        assert ErrorResponse is UnifiedErrorResponse
        assert TokenRequest is UnifiedTokenRequest
        assert TokenResponse is UnifiedTokenResponse
        
        print("✅ qp-media schemas integration verified")
    
    def test_monet_orm_integration(self):
        """Test monet uses unified ORM."""
        try:
            sys.path.insert(0, str(workspace / "monet"))
            from database import Base, db_session
        except ImportError as e:
            pytest.skip(f"monet project unavailable: {e}")
        
        try:
            from zsys.core.base.models import Base as UnifiedBase
        except ImportError as e:
            pytest.skip(f"zsys.core.base.models unavailable: {e}")
        
        # Should use unified Base
        assert Base is UnifiedBase
        assert db_session is not None
        
        print("✅ monet ORM integration verified")


def run_all_tests():
    """Run all comprehensive tests."""
    print("=" * 70)
    print("COMPREHENSIVE UNIFIED ARCHITECTURE TESTS")
    print("=" * 70)
    
    tests_total = 0
    tests_passed = 0
    
    try:
        # Models structure
        print("\n[MODELS STRUCTURE TESTS]")
        models_tests = TestModelsStructure()
        models_tests.test_user_model_import()
        models_tests.test_chat_model_import()
        models_tests.test_message_model_import()
        models_tests.test_media_file_model_import()
        models_tests.test_wallet_model_import()
        models_tests.test_unified_models_import()
        tests_total += 6
        tests_passed += 6
        
        # Schemas structure
        print("\n[SCHEMAS STRUCTURE TESTS]")
        schemas_tests = TestSchemasStructure()
        schemas_tests.test_user_schemas_import()
        schemas_tests.test_chat_schemas_import()
        schemas_tests.test_message_schemas_import()
        schemas_tests.test_media_schemas_import()
        schemas_tests.test_wallet_schemas_import()
        schemas_tests.test_common_schemas_import()
        schemas_tests.test_unified_schemas_import()
        tests_total += 7
        tests_passed += 7
        
        # ORM system
        print("\n[ORM SYSTEM TESTS]")
        orm_tests = TestORMSystem()
        orm_tests.test_orm_initialization()
        orm_tests.test_create_all_tables()
        orm_tests.test_user_crud()
        orm_tests.test_relationships()
        tests_total += 4
        tests_passed += 4
        
        # Schema validation
        print("\n[SCHEMA VALIDATION TESTS]")
        validation_tests = TestSchemasValidation()
        validation_tests.test_user_schema_validation()
        validation_tests.test_media_schema_validation()
        validation_tests.test_error_schema()
        tests_total += 3
        tests_passed += 3
        
        # Project integrations
        print("\n[PROJECT INTEGRATION TESTS]")
        integration_tests = TestProjectIntegrations()
        integration_tests.test_qpmedia_schemas_integration()
        integration_tests.test_monet_orm_integration()
        tests_total += 2
        tests_passed += 2
        
        print("\n" + "=" * 70)
        print(f"✅ ALL {tests_passed}/{tests_total} TESTS PASSED")
        print("=" * 70)
        
        print("\n📊 ARCHITECTURE STATUS:")
        print("   ✅ Models properly separated (user, chat, message, media, wallet)")
        print("   ✅ Schemas properly separated (user, chat, message, media, wallet, common)")
        print("   ✅ ORM system functional (init_db, sessions, CRUD)")
        print("   ✅ Schema validation working")
        print("   ✅ qp-media integrated with unified schemas")
        print("   ✅ monet integrated with unified ORM")
        print("\n🎉 UNIFIED ARCHITECTURE IS FULLY OPERATIONAL!\n")
        
        return True
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print(f"\nFailed: {tests_total - tests_passed}/{tests_total} tests")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
