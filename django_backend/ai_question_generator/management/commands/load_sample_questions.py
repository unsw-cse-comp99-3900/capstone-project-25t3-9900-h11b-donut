"""
管理命令：加载示例测试数据
python manage.py load_sample_questions
"""
from django.core.management.base import BaseCommand
from ai_question_generator.models import SampleQuestion


class Command(BaseCommand):
    help = '加载AI题目生成的示例测试数据'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('清除现有示例数据...'))
        SampleQuestion.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('加载Python Data Structures示例数据...'))
        
        # Python Data Structures 示例题目
        python_samples = [
            {
                'course_code': 'COMP9900',
                'topic': 'Python Data Structures',
                'difficulty': 'medium',
                'question_type': 'mcq',
                'question_text': 'What is the time complexity of accessing an element in a Python list by index?',
                'options': [
                    'A. O(1)',
                    'B. O(n)',
                    'C. O(log n)',
                    'D. O(n²)'
                ],
                'correct_answer': 'A',
                'explanation': 'List access by index is O(1) because Python lists are implemented as dynamic arrays with direct memory access.',
                'score': 10,
                'created_by': 'system'
            },
            {
                'course_code': 'COMP9900',
                'topic': 'Python Data Structures',
                'difficulty': 'medium',
                'question_type': 'short_answer',
                'question_text': 'Explain the difference between a list and a tuple in Python. Provide at least three key differences.',
                'sample_answer': 'The main differences are: 1) Mutability - lists are mutable (can be modified) while tuples are immutable (cannot be changed after creation). 2) Performance - tuples are generally faster than lists due to their immutability. 3) Syntax - lists use square brackets [] while tuples use parentheses (). 4) Use cases - lists are used for homogeneous collections that may change, tuples for heterogeneous data that should remain constant.',
                'grading_points': [
                    'Mutability difference (lists mutable, tuples immutable)',
                    'Performance comparison (tuples faster)',
                    'Syntax difference ([] vs ())',
                    'Use case scenarios (when to use each)'
                ],
                'score': 10,
                'created_by': 'system'
            }
        ]
        
        for sample in python_samples:
            SampleQuestion.objects.create(**sample)
        
        self.stdout.write(self.style.SUCCESS('✅ 成功加载Machine Learning示例数据...'))
        
        # Machine Learning 示例题目
        ml_samples = [
            {
                'course_code': 'COMP9900',
                'topic': 'Machine Learning Basics',
                'difficulty': 'medium',
                'question_type': 'mcq',
                'question_text': 'What is the primary purpose of a learning rate in gradient descent optimization?',
                'options': [
                    'A. To determine the batch size during training',
                    'B. To control the step size when updating model parameters',
                    'C. To set the number of training epochs',
                    'D. To initialize model weights'
                ],
                'correct_answer': 'B',
                'explanation': 'The learning rate controls how much we adjust the model parameters with respect to the loss gradient. A larger learning rate means bigger steps, while a smaller learning rate means smaller, more careful steps.',
                'score': 10,
                'created_by': 'system'
            },
            {
                'course_code': 'COMP9900',
                'topic': 'Machine Learning Basics',
                'difficulty': 'medium',
                'question_type': 'short_answer',
                'question_text': 'Explain what happens when the learning rate is too high versus too low in neural network training. What are the consequences of each scenario?',
                'sample_answer': 'When the learning rate is too high, the model parameters can overshoot the optimal values, causing the loss to oscillate or even diverge, preventing the model from converging to a good solution. The training may become unstable and the loss might increase instead of decrease. When the learning rate is too low, the model learns very slowly, requiring many more iterations to converge. This increases training time significantly and the model might get stuck in local minima or plateaus, never reaching the global optimum within a reasonable time frame.',
                'grading_points': [
                    'High learning rate causes overshooting and oscillation',
                    'High learning rate can lead to divergence/instability',
                    'Low learning rate causes slow convergence',
                    'Low learning rate increases training time',
                    'Low learning rate may get stuck in local minima'
                ],
                'score': 10,
                'created_by': 'system'
            }
        ]
        
        for sample in ml_samples:
            SampleQuestion.objects.create(**sample)
        
        total = SampleQuestion.objects.count()
        self.stdout.write(self.style.SUCCESS(f'✅ 成功加载 {total} 个示例题目！'))
        
        # 显示统计
        for topic in ['Python Data Structures', 'Machine Learning Basics']:
            count = SampleQuestion.objects.filter(topic=topic).count()
            self.stdout.write(f'  - {topic}: {count} 题')
