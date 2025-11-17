    
    def generate_welcome_response(self) -> str:
        """生成固定的欢迎回复"""
        return """
        <div>
            <div style="font-weight: 700; margin-bottom: 8px;">
                Hello! 👋 I'm your AI Learning Coach.
            </div>
            <div style="line-height: 1.6;">
                I'd love to help you with that! 🤔
                <br /><br />
                To give you the best assistance, could you tell me a bit more about what you're working on?
                <br /><br />
                You can ask me about:
                <ul style="padding-left: 18px; margin: 8px 0;">
                    <li>Your study plan and schedule</li>
                    <li>Specific tasks or assignments</li>
                    <li>Practice exercises for difficult topics</li>
                    <li>Or just ask for some encouragement!</li>
                </ul>
            </div>
        </div>
        """