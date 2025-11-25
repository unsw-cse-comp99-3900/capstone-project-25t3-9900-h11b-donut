import { useEffect, useState } from 'react'
import { aiQuestionService, type GeneratedQuestion } from '../../services/aiQuestionService'

interface PracticeSessionProps {
  course: string
  topic: string
  sessionId: string
  onSubmitSuccess?: (sessionId: string) => void //Callback after successful submission
  onClose?: () => void //Close the callback of the pop-up window
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
   //First, check if the answer has been submitted
    const checkSubmissionStatus = async () => {
      try {
        const studentId = localStorage.getItem('current_user_id');
        const token = localStorage.getItem('auth_token');
        
        if (!studentId) {
          throw new Error('User not logged in');
        }

        //Query the submission records of this session
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
          //Already submitted, reconstructed result data
            console.log('✅ Detected submitted answer, loading result:', resultsData.results);
            
            // Key fix: Even if submitted, the question data must still be loaded to display the complete question stem
            await fetchQuestions();
            
            // Extract rating results from submission records
            const gradingResults = resultsData.results.map((r: any) => r.grading_result);
            
            // Calculate the total score
            const totalScore = gradingResults.reduce((sum: number, r: any) => sum + (r.score || 0), 0);
            const totalMaxScore = gradingResults.reduce((sum: number, r: any) => sum + (r.max_score || 0), 0);
            const percentage = totalMaxScore > 0 ? (totalScore / totalMaxScore * 100) : 0;
            
            // Set the result status and directly display the result page
            setResults({
              success: true,
              student_id: studentId,
              grading_results: gradingResults,
              total_score: totalScore,
              total_max_score: totalMaxScore,
              percentage: percentage
            });
            
            // IsLoading will be set to false in fetchQuestions
            return;
          }
        }
        
        // No submission record, continue loading questions
        await fetchQuestions();
        
      } catch (err) {
        console.error('Error checking submission status:', err);
        // Attempting to load questions even when errors occur
        await fetchQuestions();
      }
    };

    // Retrieve the title from the API
    const fetchQuestions = async () => {
      try {
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
        
        console.log('🔍 [PracticeSession] Original API response:', data)
        
        if (data.success) {
          // Convert data format to match front-end interface
          const formattedQuestions: GeneratedQuestion[] = data.questions.map((q: any) => ({
            id: q.id,
            question_type: q.question_type,
            question_data: q.question_data,
            difficulty: q.difficulty || 'medium'
          }))
          
          console.log('✅ [PracticeSession] Formatted question array:', formattedQuestions)
          console.log('📊 [PracticeSession] number of questions:', formattedQuestions.length)
          console.log('📝 [PracticeSession] Details of the first question:', formattedQuestions[0])
          
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

      const studentId = localStorage.getItem('current_user_id');
      console.log('🔍 localStorage 中的 current_user_id:', studentId);
      
      if (!studentId) {
        setError('User not logged in. Please refresh the page and try again.');
        setIsSubmitting(false);
        return;
      }
      
      // Submit the answer to the backend
      const submitData = {
        session_id: sessionId,
        student_id: studentId, 
        answers: Object.entries(answers).map(([questionId, answer]) => ({
          question_db_id: parseInt(questionId, 10), 
          answer: answer,
          time_spent: 30 
        }))
      }

      console.log('📤 Submit answer data:', submitData)
      const response = await aiQuestionService.submitAnswers(submitData as any)
      console.log('📥 Submit answer response:', response)
      
      if (response.success) {
        setResults(response)
        if (onSubmitSuccess) {
          onSubmitSuccess(sessionId)
        }
      } else {
        console.error('❌ submit fail:', response.error || response.message)
        setError(response.message || 'Failed to submit answers')
      }
    } catch (err) {
      console.error('❌ Abnormal submission of answers:', err)
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

  // Error state 
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
              onClose(); // close pop-up
            } else {
              window.location.hash = '#/chat-window'; //Backup plan
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

  // Results state
  if (results) {
    // If the results have values but the questions have not been loaded yet, display 'Loading'
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
    
    //  Fix: no longer distinguishing isReviewMode, as question data is always loaded now
    
    //  Calculate the total score and percentage
    const totalScore = results.total_score || 0;
    const totalMaxScore = results.total_max_score || 0;
    const percentage = totalMaxScore > 0 ? (totalScore / totalMaxScore * 100) : 0;
    
    // Debugging: View the results data structure
    console.log('🔍 [Results Page] result data:', {
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
              {/*  Unified display logic: always use the questions array (now ensured to load) */}
              {questions.map((question, index) => {
                // Find the corresponding rating result based on the question.id
                const result = results.grading_results?.find((r: any) => r.question_id === question.id)
                
                if (!result) {
                  console.warn(`⚠️ cannot find ${question.id} grading result`)
                  return null
                }
                
                const isShortAnswer = question.question_type === 'short_answer'
                const isMCQ = question.question_type === 'mcq'
                const questionData = question.question_data
                const questionText = questionData?.question
                const options = questionData?.options
                const sampleAnswer = questionData?.sample_answer
                const correctAnswer = questionData?.correct_answer
                
                //  The analysis of multiple-choice questions can be found in questionData.exe, while the analysis of short answer questions can be found in result.solution
                const explanation = isMCQ ? questionData?.explanation : result.solution
                
                //  Determine the level based on the score range
                const score = result.score || 0;
                const maxScore = result.max_score || 10;
                let label = 'Incorrect';
                let bgColor = '#FEE2E2';
                let textColor = '#991B1B';
                
                if (score >= maxScore) {
                  // fullmark：Correct
                  label = 'Correct';
                  bgColor = '#D1FAE5';
                  textColor = '#065F46';
                } else if (score >= 4) {
                  // 4-9：Partly Correct
                  label = 'Partly Correct';
                  bgColor = '#FEF3C7';
                  textColor = '#92400E';
                }
                // 0-3：Incorrect（default mark）
                
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
                    
                    {/* shortanswer - always display*/}
                    <div style={{
                      fontSize: '15px',
                      fontWeight: 600,
                      color: '#172239',
                      marginBottom: '12px',
                      lineHeight: 1.5
                    }}>
                      {questionText}
                    </div>
                    
                    {/* Multiple Choice Question: Display Options */}
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
                            
                            // Fix: The correct answer is a letter (such as "B"), which needs to be converted into an index for comparison
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
                    
                    {/* Short answer: Display student answers and reference answers */}
                    {isShortAnswer && (
                      <div>
                        {/* answer*/}
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
                        
                        {/* standard answer */}
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
                    
                    {/* analysis */}
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
                  onClose(); 
                } else {
                  window.location.hash = '#/chat-window'; 
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
  

  const currentQuestionData = question?.question_data
  const questionText = currentQuestionData?.question  
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

  // Main quiz UI 
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

          {/* 🔍 adjustment */}
          {console.log('🔍 [Determination of question type]', {
            question_type: question.question_type,
            isMCQ: question.question_type === 'mcq',
            isShort: question.question_type === 'short',
            hasOptions: !!options,
            optionsLength: options?.length
          })}

          {question.question_type === 'mcq' && options && options.length > 0 && (
            <div style={{ display: 'grid', gap: '12px' }}>
              {options.map((option, i) => {
                // Check if the option already contains a letter prefix (such as "A.")
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
