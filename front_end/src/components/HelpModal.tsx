
interface HelpModalProps {
  isOpen: boolean
  onClose: () => void
}

export function HelpModal({ isOpen, onClose }: HelpModalProps) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="help-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose} aria-label="Back">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M11 14L5 8L11 2" stroke="#161616" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        
        <h2 className="help-title">
          <span className="help-icon">📚</span>
          How to Use AI Study Planner
        </h2>
        
        <div className="help-content">
          <div className="help-sections">
            <section className="help-section">
              <h3>🎯 Getting Started</h3>
              <ul>
                <li><strong>Login:</strong> Enter your student ID and password to access the system</li>
                <li><strong>Dashboard:</strong> View your courses, deadlines, and AI-generated study plans</li>
                <li><strong>Navigation:</strong> Use the sidebar to switch between different sections</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>📅 Study Plans</h3>
              <ul>
                <li><strong>Generate Plan:</strong> Click "Generate AI Plan" to create personalized study schedules</li>
                <li><strong>View Plans:</strong> Browse weekly plans with detailed task breakdowns</li>
                <li><strong>Mark Progress:</strong> Check off completed tasks to track your progress and earn bonus rewards</li>
                <li><strong>Adjust Settings:</strong> Customize study hours and preferred days</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>🤖 AI Coach</h3>
              <ul>
                <li><strong>Start Chat:</strong> Click "Start Chat" to talk with your AI learning coach</li>
                <li><strong>Ask Questions:</strong> Seek encouragement, support, and discuss any learning challenges you're facing</li>
                <li><strong>Plan Explanation:</strong> Ask "explain my plan" to understand your study schedule</li>
                <li><strong>Practice Help:</strong> Request practice questions for topics you find difficult</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>📝 Practice Questions</h3>
              <ul>
                <li><strong>Generate Questions:</strong> Create practice problems based on your course materials</li>
                <li><strong>Question Types:</strong> AI generates questions with 60% multiple choice and 40% short answer</li>
                <li><strong>Question Number:</strong> You can choose how many questions to generate</li>
                <li><strong>Difficulty Level:</strong> Customizable difficulty (easy, medium, hard)</li>
                <li><strong>Instant Feedback:</strong> Get AI-powered grading and explanations</li>
                <li><strong>Ask Coach:</strong> Request additional clarification about practice questions from your AI coach</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>⚙️ Settings & Preferences</h3>
              <ul>
                <li><strong>Daily Hours:</strong> Set how many hours you want to study per day</li>
                <li><strong>Weekly Study Days:</strong> Choose which days of the week you prefer to study</li>
                <li><strong>Avoid Days:</strong> Mark weekends or specific days as rest days</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>💡 Pro Tips</h3>
              <ul>
                <li><strong>Be Realistic:</strong> Set achievable daily study goals</li>
                <li><strong>Regular Updates:</strong> Remember to "Generate new plans" if deadlines change</li>
                <li><strong>Track Progress:</strong> Mark completed tasks to stay motivated</li>
                <li><strong>Ask for Help:</strong> Use AI Coach whenever you're stuck</li>
                <li><strong>Practice Regularly:</strong> Generate questions to test your understanding</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>🔧 Troubleshooting</h3>
              <ul>
                <li><strong>Slow Loading:</strong> Refresh the page or check your internet connection</li>
                <li><strong>AI Not Responding:</strong> Wait a few moments and try again</li>
                <li><strong>Login Issues:</strong> Check your student ID and password</li>
                <li><strong>Missing Courses:</strong> Add courses manually if they don't appear</li>
              </ul>
            </section>
          </div>
        </div>
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.2);
          backdrop-filter: saturate(180%) blur(2px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          padding: 20px;
        }

        .help-modal {
          background: white;
          border-radius: 20px;
          border: 2px solid #F6B48E;
          max-width: 700px;
          max-height: 80vh;
          width: 100%;
          box-shadow: 0 24px 48px rgba(0, 0, 0, 0.12);
          position: relative;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .close-btn {
          position: absolute;
          top: 12px;
          left: 12px;
          background: #fff;
          border: 1px solid #EAEAEA;
          border-radius: 999px;
          width: 36px;
          height: 36px;
          display: grid;
          place-items: center;
          cursor: pointer;
          color: #6b7280;
          transition: all 0.2s ease;
          font-size: 18px;
        }

        .close-btn:hover {
          background: #f8f9fb;
          border-color: #DCE3EE;
        }

        .help-title {
          text-align: center;
          font-weight: 800;
          font-size: 22px;
          margin: 0;
          padding: 28px 28px 20px 28px;
          color: #172239;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          flex-shrink: 0;
          border-bottom: 1px solid #f0f2f7;
        }

        .help-icon {
          font-size: 22px;
        }

        .help-content {
          padding: 20px 28px 28px 28px;
          overflow-y: auto;
          flex: 1;
        }

        .help-sections {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .help-section {
          background: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 20px;
        }

        .help-section h3 {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 12px;
          color: #374151;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .help-section ul {
          margin: 0;
          padding-left: 20px;
          color: #4b5563;
        }

        .help-section li {
          margin-bottom: 8px;
          line-height: 1.5;
        }

        .help-section strong {
          color: #1f2937;
          font-weight: 600;
        }

        @media (max-width: 768px) {
          .modal-overlay {
            padding: 16px;
          }

          .help-content {
            padding: 24px 20px;
          }

          .help-section {
            padding: 16px;
          }

          .help-title {
            font-size: 20px;
          }
        }
      `}</style>
    </div>
  )
}