// 使用简单的X符号代替图标库

interface HelpModalProps {
  isOpen: boolean
  onClose: () => void
}

export function HelpModal({ isOpen, onClose }: HelpModalProps) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="help-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>
          ✕
        </button>
        
        <div className="help-content">
          <h2 className="help-title">
            <span className="help-icon">📚</span>
            How to Use AI Study Planner
          </h2>
          
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
                <li><strong>Mark Progress:</strong> Check off completed tasks to track your progress</li>
                <li><strong>Adjust Settings:</strong> Customize study hours and preferred days</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>🤖 AI Coach</h3>
              <ul>
                <li><strong>Start Chat:</strong> Click "Start Chat" to talk with your AI learning coach</li>
                <li><strong>Ask Questions:</strong> Get help with assignments, study strategies, and course concepts</li>
                <li><strong>Plan Explanation:</strong> Ask "explain my plan" to understand your study schedule</li>
                <li><strong>Practice Help:</strong> Request practice questions for topics you find difficult</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>📝 Practice Questions</h3>
              <ul>
                <li><strong>Generate Questions:</strong> Create practice problems based on your course materials</li>
                <li><strong>Question Types:</strong> Choose from multiple choice, short answer, or coding problems</li>
                <li><strong>Difficulty Levels:</strong> Select easy, medium, or hard questions</li>
                <li><strong>Instant Feedback:</strong> Get AI-powered grading and explanations</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>⚙️ Settings & Preferences</h3>
              <ul>
                <li><strong>Study Hours:</strong> Set how many hours you want to study per day</li>
                <li><strong>Study Days:</strong> Choose which days of the week you prefer to study</li>
                <li><strong>Break Days:</strong> Mark weekends or specific days as rest days</li>
                <li><strong>Time Zone:</strong> Ensure deadlines and plans are in your local time</li>
              </ul>
            </section>

            <section className="help-section">
              <h3>💡 Pro Tips</h3>
              <ul>
                <li><strong>Be Realistic:</strong> Set achievable daily study goals</li>
                <li><strong>Regular Updates:</strong> Generate new plans weekly as deadlines change</li>
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

          <div className="help-footer">
            <p className="help-note">
              Need more help? Contact your system administrator or check the FAQ section.
            </p>
            <button className="btn-primary" onClick={onClose}>
              Got it, thanks!
            </button>
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
          background: rgba(0, 0, 0, 0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          padding: 20px;
        }

        .help-modal {
          background: white;
          border-radius: 12px;
          max-width: 700px;
          max-height: 80vh;
          width: 100%;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
          position: relative;
          overflow: hidden;
        }

        .close-btn {
          position: absolute;
          top: 16px;
          right: 16px;
          background: #f3f4f6;
          border: none;
          border-radius: 6px;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          color: #6b7280;
          transition: all 0.2s ease;
        }

        .close-btn:hover {
          background: #e5e7eb;
          color: #374151;
        }

        .help-content {
          padding: 32px;
          max-height: calc(80vh - 64px);
          overflow-y: auto;
        }

        .help-title {
          font-size: 24px;
          font-weight: 700;
          margin-bottom: 24px;
          display: flex;
          align-items: center;
          gap: 8px;
          color: #1f2937;
        }

        .help-icon {
          font-size: 28px;
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

        .help-footer {
          margin-top: 24px;
          padding-top: 20px;
          border-top: 1px solid #e5e7eb;
          text-align: center;
        }

        .help-note {
          color: #6b7280;
          margin-bottom: 16px;
          font-size: 14px;
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