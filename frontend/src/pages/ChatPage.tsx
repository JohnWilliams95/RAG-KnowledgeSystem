import { useRef, useEffect, useState } from 'react'
import { Input, Button, List, Avatar, Space, Typography, Spin } from 'antd'
import { SendOutlined, DeleteOutlined, PlusOutlined, SettingOutlined } from '@ant-design/icons'
import { useChatStore, type Message } from '@/stores/chatStore'
import ReactMarkdown from 'react-markdown'

const { Text } = Typography

function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 16,
      padding: '0 16px',
    }}>
      {!isUser && (
        <Avatar style={{ backgroundColor: '#52c41a', marginRight: 8 }}>AI</Avatar>
      )}
      <div style={{
        maxWidth: '75%',
        padding: '12px 16px',
        borderRadius: 12,
        backgroundColor: isUser ? '#1677ff' : '#f5f5f5',
        color: isUser ? '#fff' : '#000',
        wordBreak: 'break-word',
      }}>
        {isUser ? (
          <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
        ) : (
          <div className="markdown-body">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
        {message.isStreaming && (
          <span style={{ animation: 'blink 1s infinite' }}>▊</span>
        )}
      </div>
      {isUser && (
        <Avatar style={{ backgroundColor: '#1677ff', marginLeft: 8 }}>U</Avatar>
      )}
    </div>
  )
}

export default function ChatPage() {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const {
    currentMessages,
    currentConversation,
    isStreaming,
    sendMessage,
    createConversation,
    clearCurrentHistory,
    conversationList,
    switchConversation,
    deleteConversation,
  } = useChatStore()

  const messages = currentMessages()
  const convList = conversationList()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const text = inputValue.trim()
    if (!text || isStreaming) return
    setInputValue('')
    await sendMessage(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Conversation List */}
      <div style={{
        width: 240,
        borderRight: '1px solid #f0f0f0',
        display: 'flex',
        flexDirection: 'column',
        background: '#fafafa',
      }}>
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <Text strong>对话历史</Text>
          <Button
            type="text"
            icon={<PlusOutlined />}
            onClick={() => createConversation()}
          />
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
          {convList.map((conv) => (
            <div
              key={conv.id}
              onClick={() => switchConversation(conv.id)}
              style={{
                padding: '10px 12px',
                borderRadius: 8,
                cursor: 'pointer',
                marginBottom: 4,
                background: conv.id === currentConversation()?.id ? '#e6f4ff' : 'transparent',
                borderLeft: conv.id === currentConversation()?.id ? '3px solid #1677ff' : '3px solid transparent',
                position: 'relative',
              }}
            >
              <div style={{
                fontSize: 13,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                paddingRight: 24,
              }}>
                {conv.title}
              </div>
              <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                {conv.messages.length} 条消息
              </div>
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={(e) => {
                  e.stopPropagation()
                  deleteConversation(conv.id)
                }}
                style={{
                  position: 'absolute',
                  top: 8,
                  right: 4,
                  opacity: 0.5,
                }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div style={{
          padding: '12px 20px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#fff',
        }}>
          <Text strong style={{ fontSize: 16 }}>
            {currentConversation()?.title || '新对话'}
          </Text>
          <Space>
            <Button
              icon={<DeleteOutlined />}
              onClick={() => clearCurrentHistory()}
              disabled={messages.length === 0}
            >
              清空
            </Button>
          </Space>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '20px 0',
          background: '#fff',
        }}>
          {messages.length === 0 ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#999',
            }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>💬</div>
              <Text style={{ fontSize: 18, marginBottom: 8 }}>RAG 知识库问答</Text>
              <Text type="secondary">基于您的知识库文档，智能回答问题</Text>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid #f0f0f0',
          background: '#fff',
        }}>
          <div style={{
            display: 'flex',
            gap: 12,
            background: '#f5f5f5',
            borderRadius: 12,
            padding: '8px 8px 8px 16px',
            border: '1px solid #d9d9d9',
          }}>
            <Input.TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
              autoSize={{ minRows: 1, maxRows: 4 }}
              bordered={false}
              style={{ background: 'transparent' }}
              disabled={isStreaming}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!inputValue.trim() || isStreaming}
              style={{ borderRadius: 8 }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
