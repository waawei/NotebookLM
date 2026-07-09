"""
P0 功能测试脚本
测试所有 P0 功能的后端 API
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"


def test_health_check():
    """测试健康检查"""
    print("\n🧪 Test 1: Health Check")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_document_list():
    """测试文档列表"""
    print("\n🧪 Test 2: Document List")
    try:
        response = requests.get(f"{API_BASE_URL}/api/documents/list")
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"   Total documents: {data['total']}")

        # 检查文档是否有 summary 字段
        if data['documents']:
            doc = data['documents'][0]
            has_summary = 'summary' in doc
            print(f"   📝 Document has summary: {has_summary}")
            if has_summary and doc['summary']:
                print(f"   Summary preview: {doc['summary'][:100]}...")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_suggest_questions():
    """测试建议问题生成"""
    print("\n🧪 Test 3: Suggested Questions")

    # 先获取文档列表
    try:
        response = requests.get(f"{API_BASE_URL}/api/documents/list")
        docs = response.json()['documents']

        if not docs:
            print("⚠️  No documents available. Please upload a document first.")
            return False

        doc_ids = [doc['doc_id'] for doc in docs[:1]]  # 取第一个文档

        # 调用建议问题 API
        response = requests.post(
            f"{API_BASE_URL}/api/chat/suggest-questions",
            json=doc_ids
        )

        print(f"✅ Status: {response.status_code}")
        data = response.json()
        questions = data.get('questions', [])

        print(f"   💡 Generated {len(questions)} questions:")
        for i, q in enumerate(questions, 1):
            print(f"      {i}. {q}")

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_chat_with_citations():
    """测试对话和引用编号"""
    print("\n🧪 Test 4: Chat with Citation Numbers")

    # 先获取文档列表
    try:
        response = requests.get(f"{API_BASE_URL}/api/documents/list")
        docs = response.json()['documents']

        if not docs:
            print("⚠️  No documents available. Please upload a document first.")
            return False

        doc_ids = [doc['doc_id'] for doc in docs[:1]]

        # 发送测试问题
        chat_request = {
            "question": "What is this document about?",
            "doc_ids": doc_ids,
            "conversation_id": None,
            "history": []
        }

        response = requests.post(
            f"{API_BASE_URL}/api/chat/ask",
            json=chat_request
        )

        print(f"✅ Status: {response.status_code}")
        data = response.json()

        print(f"   📝 Answer: {data['answer'][:150]}...")
        print(f"   🔗 Citations count: {len(data['citations'])}")

        # 检查引用编号
        for citation in data['citations']:
            if 'number' in citation:
                print(f"      [{citation['number']}] {citation['doc_name']} (Score: {citation['relevance_score']:.2f})")
            else:
                print(f"      ❌ Citation missing 'number' field!")
                return False

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_conversation_persistence():
    """测试对话持久化"""
    print("\n🧪 Test 5: Conversation Persistence")

    try:
        # 获取对话列表
        response = requests.get(f"{API_BASE_URL}/api/chat/conversations")
        print(f"✅ Status: {response.status_code}")

        data = response.json()
        conversations = data.get('conversations', [])

        print(f"   💾 Total conversations: {len(conversations)}")

        if conversations:
            conv = conversations[0]
            print(f"   Last conversation:")
            print(f"      ID: {conv['id'][:8]}...")
            print(f"      Messages: {conv['message_count']}")
            print(f"      Last message: {conv['last_message'][:50] if conv['last_message'] else 'N/A'}...")

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    print("=" * 60)
    print("🚀 NotebookLM Clone - P0 Features Test Suite")
    print("=" * 60)

    # 运行所有测试
    tests = [
        test_health_check,
        test_document_list,
        test_suggest_questions,
        test_chat_with_citations,
        test_conversation_persistence
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)
        time.sleep(0.5)  # 避免 API 过载

    # 总结
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All P0 features are working correctly!")
    else:
        print("\n⚠️  Some tests failed. Please check the logs above.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
