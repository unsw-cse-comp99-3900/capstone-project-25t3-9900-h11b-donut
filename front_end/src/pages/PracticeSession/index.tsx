import { useEffect, useState } from 'react'
import { aiQuestionService, type GeneratedQuestion } from '../../services/aiQuestionService'

interface PracticeSessionProps {
  course: string
  topic: string
  sessionId: string
  onSubmitSuccess?: (sessionId: string) => void // 提交成功后的回调
  onClose?: () => void // 关闭弹窗的回调
}

export function PracticeSession({ course, topic, sessionId, onSubmitSuccess, onClose }: PracticeSessionProps) {
  const [questions, setQuestions] = useState<GeneratedQuestion[]>([])
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<{ [key: number]: string }>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // 先检查是否已经提交过答案
    const checkSubmissionStatus = async () => {
      try {
        const studentId = localStorage.getItem('current_user_id');
        const token = localStorage.getItem('auth_token');
        
        if (!studentId) {
          throw new Error('User not logged in');
        }

        // 查询该 session 的提交记录
        const resultsResponse = await fetch(
          `/api/ai/results?student_id=${studentId}&session_id=${sessionId}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          }
        );

        if (resultsResponse.ok) {
          const resultsData = await resultsResponse.json();
          
          if (resultsData.success && resultsData.results && resultsData.results.length > 0) {
            // 已经提交过，重建结果数据
            console.log('✅ 检测到已提交的答案，加载结果:', resultsData.results);
            
            // 🔥 关键修复：即使已提交，也要加载题目数据，以便显示完整的题干
            await fetchQuestions();
            
            // 从提交记录中提取评分结果
            const gradingResults = resultsData.results.map((r: any) => r.grading_result);
            
            // 计算总分
            const totalScore = gradingResults.reduce((sum: number, r: any) => sum + (r.score || 0), 0);
            const totalMaxScore = gradingResults.reduce((sum: number, r: any) => sum + (r.max_score || 0), 0);
            const percentage = totalMaxScore > 0 ? (totalScore / totalMaxScore * 100) : 0;
            
            // 设置结果状态，直接显示结果页面
            setResults({
              success: true,
              student_id: studentId,
              grading_results: gradingResults,
              total_score: totalScore,
              total_max_score: totalMaxScore,
              percentage: percentage
            });
            
            // isLoading 会在 fetchQuestions 中设置为 false
            return;
          }
        }
        
        // 没有提交记录，继续加载题目
        await fetchQuestions();
        
      } catch (err) {
        console.error('Error checking submission status:', err);
        // 出错时仍然尝试加载题目
        await fetchQuestions();
      }
    };

    // 从API获取题目
    const fetchQuestions = async () => {
      try {
        // 从后端获取生成的题目，带上认证token
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`/api/ai/questions/session/${sessionId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        })
        
        if (!response.ok) {
          throw new Error('Failed to fetch questions')
        }
        
        const data = await response.json()
        
        console.log('🔍 [PracticeSession] 原始API响应:', data)
        
        if (data.success) {
          // 转换数据格式以匹配前端接口
          const formattedQuestions: GeneratedQuestion[] = data.questions.map((q: any) => ({
            id: q.id,
            question_type: q.question_type,
            question_data: q.question_data,
            difficulty: q.difficulty || 'medium'
          }))
          
          console.log('✅ [PracticeSession] 格式化后的题目数组:', formattedQuestions)
          console.log('📊 [PracticeSession] 题目数量:', formattedQuestions.length)
          console.log('📝 [PracticeSession] 第一题详情:', formattedQuestions[0])
          
          setQuestions(formattedQuestions)
        } else {
          throw new Error(data.error || 'Failed to load questions')
        }
        
        setIsLoading(false)
      } catch (err) {
        console.error('Error fetching questions:', err)
        setError('Failed to load questions')
        setIsLoading(false)
      }
    }

    checkSubmissionStatus();
  }, [sessionId])

  const handleAnswerChange = (questionId: number, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }))
  }

  const handleSubmit = async () => {
    if (Object.keys(answers).length !== questions.length) {
      setError('Please answer all questions before submitting')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      // 获取学生ID（学号，如 z1234567）
      const studentId = localStorage.getItem('current_user_id');
      console.log('🔍 localStorage 中的 current_user_id:', studentId);
      
      if (!studentId) {
        setError('User not logged in. Please refresh the page and try again.');
        setIsSubmitting(false);
        return;
      }
      
      // 提交答案到后端
      const submitData = {
        session_id: sessionId,
        student_id: studentId,  // 直接使用字符串学号
        answers: Object.entries(answers).map(([questionId, answer]) => ({
          question_db_id: parseInt(questionId, 10),  // 后端期望 question_db_id
          answer: answer,
          time_spent: 30 // 默认30秒
        }))
      }

      console.log('📤 提交答案数据:', submitData)
      const response = await aiQuestionService.submitAnswers(submitData as any)
      console.log('📥 提交答案响应:', response)
      
      if (response.success) {
        // 后端直接返回数据在顶层，不在 data 字段中
        setResults(response)
        // 通知父组件提交成功
        if (onSubmitSuccess) {
          onSubmitSuccess(sessionId)
        }
      } else {
        console.error('❌ 提交失败:', response.error || response.message)
        setError(response.message || 'Failed to submit answers')
      }
    } catch (err) {
      console.error('❌ 提交答案异常:', err)
      setError('Failed to submit answers')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
    }
  }

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1)
    }
  }

  // Loading state - 单层卡片
  // 🔥 修复：如果已经有结果数据，即使 isLoading 也不显示 Loading（避免闪烁）
  if (isLoading && !results) {
    return (
      <div style={{
        maxWidth: '100%',
        margin: '0',
        background: 'transparent',
        borderRadius: '0',
        padding: '60px 40px',
        boxShadow: 'none',
        textAlign: 'center'
      }}>
        <div style={{
          width: '48px',
          height: '48px',
          border: '4px solid rgba(255,168,122,0.3)',
          borderTop: '4px solid #FFA87A',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 16px'
        }}></div>
        <p style={{ fontSize: '16px', opacity: 0.8, color: '#172239' }}>Loading practice questions...</p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    )
  }

  // Error state - 单层卡片
  if (error && !results) {
    return (
      <div style={{
        maxWidth: '100%',
        margin: '0',
        background: 'transparent',
        borderRadius: '0',
        padding: '40px',
        boxShadow: 'none',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
        <p style={{ fontSize: '18px', marginBottom: '24px', opacity: 0.8, color: '#172239' }}>{error}</p>
        <button 
          onClick={() => {
            if (onClose) {
              onClose(); // 关闭弹窗
            } else {
              window.location.hash = '#/chat-window'; // 备用方案
            }
          }}
          style={{
            padding: '14px 28px',
            borderRadius: '18px',
            border: '1px solid #FF9A6A',
            background: 'linear-gradient(180deg, #FFA87A 0%, #FF9F6C 100%)',
            color: '#fff',
            fontWeight: 800,
            fontSize: '16px',
            cursor: 'pointer',
            boxShadow: '0 8px 18px rgba(255,168,122,0.25)'
          }}
        >
          Back to Chat
        </button>
      </div>
    )
  }

  // Results state - 单层卡片
  if (results) {
    // 🔥 如果 results 有值但 questions 还没加载完，显示 Loading
    if (questions.length === 0) {
      return (
        <div style={{
          maxWidth: '100%',
          margin: '0',
          background: 'transparent',
          borderRadius: '0',
          padding: '60px 40px',
          boxShadow: 'none',
          textAlign: 'center'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            border: '4px solid rgba(255,168,122,0.3)',
            borderTop: '4px solid #FFA87A',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p style={{ fontSize: '16px', opacity: 0.8, color: '#172239' }}>Loading your results...</p>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      );
    }
    
    // 🔥 修复：不再区分 isReviewMode，因为现在总是会加载 questions 数据
    
    // 🔍 计算总分和百分比
    const totalScore = results.total_score || 0;
    const totalMaxScore = results.total_max_score || 0;
    const percentage = totalMaxScore > 0 ? (totalScore / totalMaxScore * 100) : 0;
    
    // 🔍 调试：查看 results 数据结构
    console.log('🔍 [Results Page] 结果数据:', {
      results,
      grading_results: results.grading_results,
      total_score: totalScore,
      total_max_score: totalMaxScore,
      calculated_percentage: percentage,
      original_percentage: results.percentage,
      questions_length: questions.length
    });
    
    return (
      <div style={{
        maxWidth: '100%',
        width: '100%',
        margin: '0',
        background: 'transparent',
        borderRadius: '0',
        padding: '40px',
        boxShadow: 'none'
      }}>

          
          <h1 style={{ fontSize: '32px', fontWeight: 800, marginBottom: '32px', textAlign: 'center', color: '#172239' }}>
            Practice Results
          </h1>
          
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <div style={{ fontSize: '64px', fontWeight: 800, color: '#FFA87A', marginBottom: '8px' }}>
              {percentage.toFixed(1)}%
            </div>
            <div style={{ fontSize: '18px', color: '#6D6D78' }}>
              Score: {totalScore} / {totalMaxScore}
            </div>
          </div>

          <div style={{ marginBottom: '32px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '12px', color: '#172239' }}>Feedback</h2>
            <p style={{ fontSize: '16px', lineHeight: 1.6, color: '#6D6D78' }}>
              {results.feedback || 'Great job completing the practice!'}
            </p>
          </div>

          <div style={{ marginBottom: '32px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '16px', color: '#172239' }}>Detailed Results</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* 🔥 统一显示逻辑：总是使用 questions 数组（现在已确保加载） */}
              {questions.map((question, index) => {
                // 根据 question.id 找到对应的评分结果
                const result = results.grading_results?.find((r: any) => r.question_id === question.id)
                
                if (!result) {
                  console.warn(`⚠️ 找不到题目 ${question.id} 的评分结果`)
                  return null
                }
                
                const isShortAnswer = question.question_type === 'short_answer'
                const isMCQ = question.question_type === 'mcq'
                const questionData = question.question_data
                const questionText = questionData?.question
                const options = questionData?.options
                const sampleAnswer = questionData?.sample_answer
                const correctAnswer = questionData?.correct_answer
                
                // 🔥 选择题的解析在 questionData.explanation，简答题的在 result.solution
                const explanation = isMCQ ? questionData?.explanation : result.solution
                
                // 🎯 根据分数段判断等级
                const score = result.score || 0;
                const maxScore = result.max_score || 10;
                let label = 'Incorrect';
                let bgColor = '#FEE2E2';
                let textColor = '#991B1B';
                
                if (score >= maxScore) {
                  // 满分：Correct
                  label = 'Correct';
                  bgColor = '#D1FAE5';
                  textColor = '#065F46';
                } else if (score >= 4) {
                  // 4-9分：Partly Correct
                  label = 'Partly Correct';
                  bgColor = '#FEF3C7';
                  textColor = '#92400E';
                }
                // 0-3分：Incorrect（默认值）
                
                return (
                  <div key={question.id} style={{
                    border: '1px solid #e7e9ef',
                    borderRadius: '14px',
                    padding: '16px',
                    background: '#fff'
                  }}>
                    {/* 题目标题 */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <span style={{ fontWeight: 700, color: '#172239' }}>Question {index + 1}</span>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        fontSize: '13px',
                        fontWeight: 700,
                        background: bgColor,
                        color: textColor
                      }}>
                        {label} • {score}/{maxScore}
                      </span>
                    </div>
                    
                    {/* 🔥 题目文本 - 始终显示 */}
                    <div style={{
                      fontSize: '15px',
                      fontWeight: 600,
                      color: '#172239',
                      marginBottom: '12px',
                      lineHeight: 1.5
                    }}>
                      {questionText}
                    </div>
                    
                    {/* 🔥 选择题：显示选项 */}
                    {isMCQ && options && options.length > 0 && (
                      <div style={{
                        marginBottom: '12px',
                        padding: '12px',
                        background: '#F9FAFB',
                        border: '1px solid #E5E7EB',
                        borderRadius: '10px'
                      }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#6B7280', marginBottom: '8px' }}>
                          📋 Options:
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {options.map((option, i) => {
                            const hasLetterPrefix = /^[A-D]\.\s*/.test(option)
                            const displayText = hasLetterPrefix ? option : `${String.fromCharCode(65 + i)}. ${option}`
                            const isStudentAnswer = result.student_answer === option
                            
                            // 🔥 修复：正确答案是字母(如"B")，需要转换成索引来比较
                            const correctAnswerLetter = String.fromCharCode(65 + i) // 'A', 'B', 'C', 'D'
                            const isCorrect = correctAnswer === correctAnswerLetter || correctAnswer === option
                            
                            return (
                              <div
                                key={i}
                                style={{
                                  fontSize: '14px',
                                  color: '#172239',
                                  padding: '6px 10px',
                                  borderRadius: '6px',
                                  background: isStudentAnswer 
                                    ? (isCorrect ? '#D1FAE5' : '#FEE2E2')
                                    : (isCorrect ? '#E0F2FE' : 'transparent'),
                                  fontWeight: (isStudentAnswer || isCorrect) ? 600 : 400
                                }}
                              >
                                {displayText}
                                {isStudentAnswer && <span style={{ marginLeft: '8px', fontSize: '12px' }}>👤 Your answer</span>}
                                {isCorrect && <span style={{ marginLeft: '8px', fontSize: '12px' }}>✅ Correct answer</span>}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                    
                    {/* 🔥 简答题：显示学生答案和参考答案 */}
                    {isShortAnswer && (
                      <div>
                        {/* 学生的答案 */}
                        {result.student_answer && (
                          <div style={{
                            marginBottom: '12px',
                            padding: '12px',
                            background: '#F9FAFB',
                            border: '1px solid #E5E7EB',
                            borderRadius: '10px'
                          }}>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: '#6B7280', marginBottom: '6px' }}>
                              📝 Your Answer:
                            </div>
                            <div style={{ fontSize: '14px', color: '#172239', lineHeight: 1.5 }}>
                              {result.student_answer}
                            </div>
                          </div>
                        )}
                        
                        {/* 参考答案 */}
                        {sampleAnswer && (
                          <div style={{
                            marginBottom: '12px',
                            padding: '12px',
                            background: '#E0F2FE',
                            border: '1px solid #BAE6FD',
                            borderRadius: '10px'
                          }}>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: '#0369A1', marginBottom: '6px' }}>
                              ✅ Sample Answer:
                            </div>
                            <div style={{ fontSize: '14px', color: '#172239', lineHeight: 1.5 }}>
                              {sampleAnswer}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* 🔥 显示解析 (对所有题型) */}
                    {explanation && (
                      <div style={{
                        marginTop: '12px',
                        padding: '12px',
                        background: '#F0F9FF',
                        border: '1px solid #BAE6FD',
                        borderRadius: '10px'
                      }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#0369A1', marginBottom: '6px' }}>
                          💡 Explanation:
                        </div>
                        <div style={{ fontSize: '14px', color: '#172239', lineHeight: 1.5 }}>
                          {explanation}
                        </div>
                      </div>
                    )}
                  </div>
                )})}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button 
              onClick={() => {
                if (onClose) {
                  onClose(); // 关闭弹窗
                } else {
                  window.location.hash = '#/chat-window'; // 备用方案
                }
              }}
              style={{
                padding: '14px 28px',
                borderRadius: '18px',
                border: '1px solid #FF9A6A',
                background: 'linear-gradient(180deg, #FFA87A 0%, #FF9F6C 100%)',
                color: '#fff',
                fontWeight: 800,
                fontSize: '16px',
                cursor: 'pointer',
                boxShadow: '0 8px 18px rgba(255,168,122,0.25)'
              }}
            >
              Back to Chat
            </button>
          </div>
        </div>
      );
  }

  const question = questions[currentQuestion]
  
  // 🔥 修复字段映射：使用新的字段名
  const currentQuestionData = question?.question_data
  const questionText = currentQuestionData?.question  // 使用 question 而不是 question_text
  const options = currentQuestionData?.options
  const sampleAnswer = currentQuestionData?.sample_answer
  const hasQuestionData = !!questionText
  
  console.log('🎯 [PracticeSession] 当前状态:', {
    questionsLength: questions.length,
    currentQuestionIndex: currentQuestion,
    currentQuestionData: question,
    hasQuestionData,
    questionText,
    questionType: question?.question_type,
    options,
    sampleAnswer
  })

  // Main quiz UI - 单层卡片
  return (
    <div style={{
      maxWidth: '100%',
      width: '100%',
      margin: '0',
      background: 'transparent',
      borderRadius: '0',
      padding: '32px',
      boxShadow: 'none'
    }}>
        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{ fontSize: '24px', fontWeight: 800, marginBottom: '8px', color: '#172239' }}>
            Practice Session
          </h1>
          <p style={{ fontSize: '16px', color: '#6D6D78', marginBottom: '16px' }}>
            {course} - {topic}
          </p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '14px', color: '#8b8f9a' }}>
              Question {currentQuestion + 1} of {questions.length}
            </span>
            <div style={{ display: 'flex', gap: '6px' }}>
              {questions.map((_, index) => (
                <div
                  key={index}
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: index === currentQuestion ? '#FFA87A' : 
                               answers[questions[index].id] ? '#A0D9A0' : '#e7e9ef'
                  }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Question */}
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{
            fontSize: '20px',
            fontWeight: 800,
            color: '#172239',
            lineHeight: 1.4,
            marginBottom: '20px'
          }}>
            {hasQuestionData ? questionText : 'Loading question...'}
          </h2>

          {/* 🔍 调试信息 */}
          {console.log('🔍 [题目类型判断]', {
            question_type: question.question_type,
            isMCQ: question.question_type === 'mcq',
            isShort: question.question_type === 'short',
            hasOptions: !!options,
            optionsLength: options?.length
          })}

          {question.question_type === 'mcq' && options && options.length > 0 && (
            <div style={{ display: 'grid', gap: '12px' }}>
              {options.map((option, i) => {
                // 检查选项是否已经包含字母前缀（如 "A. "）
                const hasLetterPrefix = /^[A-D]\.\s*/.test(option)
                const displayText = hasLetterPrefix ? option : `${String.fromCharCode(65 + i)}. ${option}`
                const isSelected = answers[question.id] === option
                return (
                  <button
                    key={i}
                    onClick={() => handleAnswerChange(question.id, option)}
                    style={{
                      padding: '16px 18px',
                      borderRadius: '14px',
                      border: isSelected ? '2px solid #FF9A6A' : '1px solid #e7e9ef',
                      background: isSelected ? 'linear-gradient(180deg, #FFF9F5 0%, #FFEBDD 100%)' : '#fff',
                      boxShadow: isSelected ? '0 6px 14px rgba(255,168,122,0.18)' : '0 2px 8px rgba(0,0,0,0.06)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <span style={{ fontSize: '15px', color: '#172239' }}>{displayText}</span>
                  </button>
                )
              })}
            </div>
          )}

          {question.question_type === 'short_answer' && (
            <textarea
              value={answers[question.id] || ''}
              onChange={(e) => handleAnswerChange(question.id, e.target.value)}
              style={{
                width: '100%',
                minHeight: '140px',
                padding: '16px',
                borderRadius: '14px',
                border: '1px solid #e7e9ef',
                background: '#fff',
                fontSize: '15px',
                lineHeight: 1.6,
                resize: 'vertical',
                fontFamily: 'inherit'
              }}
              placeholder="Enter your answer here..."
            />
          )}
        </div>

        {/* Navigation */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          alignItems: 'center',
          gap: '16px',
          marginTop: '24px'
        }}>
          <button
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
            style={{
              justifySelf: 'start',
              padding: '14px 24px',
              minWidth: '140px',
              borderRadius: '18px',
              border: '1px solid #FF9A6A',
              background: 'linear-gradient(180deg, #FFA87A 0%, #FF9F6C 100%)',
              color: '#fff',
              fontWeight: 800,
              fontSize: '16px',
              cursor: currentQuestion === 0 ? 'not-allowed' : 'pointer',
              opacity: currentQuestion === 0 ? 0.5 : 1,
              boxShadow: '0 8px 18px rgba(255,168,122,0.25)'
            }}
          >
            Previous
          </button>

          <div style={{ justifySelf: 'center', fontSize: '14px', color: '#8b8f9a' }}>
            {Object.keys(answers).length} / {questions.length} answered
          </div>

          {currentQuestion === questions.length - 1 ? (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || Object.keys(answers).length !== questions.length}
              style={{
                justifySelf: 'end',
                padding: '14px 24px',
                minWidth: '140px',
                borderRadius: '18px',
                border: '1px solid #FF9A6A',
                background: 'linear-gradient(180deg, #FFA87A 0%, #FF9F6C 100%)',
                color: '#fff',
                fontWeight: 800,
                fontSize: '16px',
                cursor: (isSubmitting || Object.keys(answers).length !== questions.length) ? 'not-allowed' : 'pointer',
                opacity: (isSubmitting || Object.keys(answers).length !== questions.length) ? 0.5 : 1,
                boxShadow: '0 8px 18px rgba(255,168,122,0.25)'
              }}
            >
              {isSubmitting ? 'Submitting...' : 'Submit'}
            </button>
          ) : (
            <button
              onClick={handleNext}
              style={{
                justifySelf: 'end',
                padding: '14px 24px',
                minWidth: '140px',
                borderRadius: '18px',
                border: '1px solid #FF9A6A',
                background: 'linear-gradient(180deg, #FFA87A 0%, #FF9F6C 100%)',
                color: '#fff',
                fontWeight: 800,
                fontSize: '16px',
                cursor: 'pointer',
                boxShadow: '0 8px 18px rgba(255,168,122,0.25)'
              }}
            >
              Next
            </button>
          )}
        </div>

        {error && (
          <div style={{
            marginTop: '20px',
            padding: '14px 18px',
            background: '#FEE2E2',
            border: '1px solid #FCA5A5',
            borderRadius: '14px',
            color: '#991B1B',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}
      </div>
  )
}
