import { useState, useEffect } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconMonitor from '../../assets/icons/bell-24.svg'
import adminHomepageImage from '../../assets/images/admin-homepage.png'
import illustrationAdmin from '../../assets/images/illustration-admin.png'
import illustrationAdmin2 from '../../assets/images/illustration-admin2.png'
import illustrationAdmin3 from '../../assets/images/illustration-admin3.png'
import illustrationAdmin4 from '../../assets/images/illustration-admin4.png'
import { apiService, type ApiQuestion } from '../../services/api'



function updateTaskStatsLocal(courseId: string, newTasks: any[]) {
  const adminId = localStorage.getItem('current_user_id');
  if (!adminId) return;

  // 更新每门课程的任务数统计
  const countsKey = `admin:${adminId}:tasks_counts_by_course`;
  const countsByCourse = JSON.parse(localStorage.getItem(countsKey) || '{}');
  countsByCourse[courseId] = newTasks.length;
  localStorage.setItem(countsKey, JSON.stringify(countsByCourse));
  
  // 更新总任务数
  const total = Object.values(countsByCourse).reduce<number>(
  (sum, n) => sum + Number(n || 0),
  0
);
  localStorage.setItem(`admin:${adminId}:tasks_total_count`, String(total));

  window.dispatchEvent(new Event('tasksUpdated'));
}
// 图片映射 - 循环使用4张图片
const adminIllustrations = [
  illustrationAdmin,
  illustrationAdmin2, 
  illustrationAdmin3,
  illustrationAdmin4
];
type NewTask = {
  title: string;
  id: string;
  deadline: string;
  brief: string;
  attachment: File | null;
  percentContribution: number;
};

export function AdminManageCourse() {
  const [uploadStatus, setUploadStatus] = useState<'idle'|'uploading'|'done'|'error'>('idle');
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);

  const resetUpload = () => {
  setUploadStatus('idle');
  setUploadedUrl(null);
  setUploadError(null);
  setFileInputKey(k => k + 1);   
  };
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<any>(null)
  const [taskModalOpen, setTaskModalOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<any>(null)
  const [deleteTaskId, setDeleteTaskId] = useState<string | null>(null)
  const [tasks, setTasks] = useState<any[]>([])
  const [materials, setMaterials] = useState<any[]>([])
  const [newTask, setNewTask] = useState({
  title: '',
  id: '',
  deadline: '',
  brief: '',
  attachment: null,   
  percentContribution: 100,
});
  const [materialModalOpen, setMaterialModalOpen] = useState(false)
  const [editingMaterial, setEditingMaterial] = useState<any>(null)
  const [deleteMaterialId, setDeleteMaterialId] = useState<string | null>(null)
  const [newMaterial, setNewMaterial] = useState<{
  name: string;
  description: string;
  file: File | null;   // ← 只能是文件
}>({
  name: '',
  description: '',
  file: null,
});
  
  // Question相关状态
  const [questionModalOpen, setQuestionModalOpen] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<any>(null)
  
  // 批量删除状态
  const [batchDeleteMode, setBatchDeleteMode] = useState(false)
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([])
  
  const [questions, setQuestions] = useState<any[]>([])
  
  // 批量题目支持：存储多个待创建的题目
  const [batchQuestions, setBatchQuestions] = useState<any[]>([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  
  const [newQuestion, setNewQuestion] = useState({
    type: 'multiple-choice', // multiple-choice 或 short-answer
    topic: '', // 主题
    title: '',
    description: '',
    keywords: '',
    questionText: '', // 题目
    options: ['', '', '', ''], // 选择题选项
    correctAnswer: '', // 选择题正确答案
    answer: '', // 简答题答案(保留用于后端兼容)
    sampleAnswer: '', // 简答题示例答案
    keyPoints: '', // 简答题关键要点
    score: 10, // 分数
    difficulty: 'Medium', // 难度: Easy, Medium, Hard
    gradingCriteria: '', // 评分标准
    hint: '' // 提示
  })

  // 文件上传状态
  const [questionFileUploading, setQuestionFileUploading] = useState(false)
  const [questionFileError, setQuestionFileError] = useState('')
  
  const [user, setUser] = useState<{ name?: string; email?: string; avatarUrl?: string } | null>(null);

  // 从URL参数获取课程ID
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.hash.split('?')[1]);
    const courseId = urlParams.get('courseId');
    const adminId = localStorage.getItem('current_user_id');

    if (courseId && adminId) {
      try {
        const savedCourses = localStorage.getItem(`admin:${adminId}:courses`);

        if (savedCourses) {
          const courses = JSON.parse(savedCourses);
          const course = courses.find((c: any) => c.id === courseId);
          if (course) {
            setSelectedCourse(course);          
            // 加载该课程的Task数据
            const savedTasks = localStorage.getItem(`admin:${adminId}:course_tasks_${courseId}`);
            if (savedTasks) {
              setTasks(JSON.parse(savedTasks));
            }           
            // 加载该课程的Material数据
            const savedMaterials = localStorage.getItem(`admin:${adminId}:course_materials_${courseId}`);
            if (savedMaterials) {
              setMaterials(JSON.parse(savedMaterials));
            }
            
            // 加载该课程的Question数据
            const savedQuestions = localStorage.getItem(`admin:${adminId}:course_questions_${courseId}`);
            if (savedQuestions) {
              setQuestions(JSON.parse(savedQuestions));
            }
          }
        }
      } catch (error) {
        console.error('Error loading course:', error);
      }
    }
  }, []);


  useEffect(() => {
  const uid = localStorage.getItem('current_user_id');
  if (uid) {
    try {
      const userData = JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null');
      if (userData) {
        setUser(userData);
      } else {
        console.warn('No user data found for current_user_id');
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  } else {
    console.warn('No current_user_id found in localStorage');
  }
}, []);
 
  
  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('login_time');
    localStorage.removeItem('current_user_id');
    window.location.hash = '#/login-admin';
  };

  const handleNavigation = (path: string) => {
    window.location.hash = path;
  };

  // 打开创建任务弹窗
  const handleAddTask = () => {
    setTaskModalOpen(true);
  };

  // 关闭创建任务弹窗
  const handleCloseTaskModal = () => {
    setTaskModalOpen(false);
    setEditingTask(null);
    setNewTask({
      title: '',
      id: '',
      deadline: '',
      brief: '',
      attachment: null,
      percentContribution: 100,
    });
    resetUpload(); 
  };

  // 处理任务表单输入
  const handleTaskInputChange = <K extends keyof NewTask>(
  field: K,
  value: NewTask[K]
) => {
  setNewTask((prev) => ({
    ...prev,
    [field]: value,
  }));
};

  // 创建新任务
  const handleCreateTask = async () => {
  // 基本校验
  if (!newTask.title?.trim()) { alert('Title is required'); return; }
  if (!selectedCourse) { alert('No course selected'); return; }
  
  // 验证deadline格式: 支持 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM 或 YYYY-MM-DDTHH:MM:SS
  if (!newTask.deadline || !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$/.test(newTask.deadline)) {
    alert('Please select a valid deadline');
    return;
  }
  
  const pct = newTask.percentContribution;
  if (
    typeof pct !== 'number' ||
    Number.isNaN(pct) ||
    pct < 1 ||
    pct > 100
  ) {
    alert('Percentage must be a number between 1 and 100');
    return;
  }
  
  // 检查deadline是否早于今天
  const today = new Date();
  const todayStr = new Date(today.getFullYear(), today.getMonth(), today.getDate())
    .toISOString()
    .slice(0, 10);
  const deadlineDate = newTask.deadline.slice(0, 10); // 提取日期部分
  if (deadlineDate < todayStr) {
    alert('Deadline ahead of today!');
    return;
  }

  // 1) 先上传附件（如果有）
  let fileUrl: string | null = null;
  const file = newTask.attachment as File | null;

  if (file) {
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('course', selectedCourse.id); // 用课程号分目录（/task/<course>/...）
      const token = localStorage.getItem('auth_token') || '';
      const uploadRes = await fetch('/api/courses_admin/upload/task-file', {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: fd,
      }).then(r => r.json());

      if (!uploadRes?.success) {
        alert(uploadRes?.message || 'Upload attachment failed');
        return;
      }
      fileUrl = uploadRes.data.url as string; // e.g. /task/COMP9900/xxx_ab12cd34.pdf
    } catch (e: any) {
      console.error('Upload error:', e);
      alert(e?.message || 'Upload attachment error');
      return;
    }
  }

  // 2) 构造创建 Task 的 payload（百分比固定 100）
  const payload = {
    title: newTask.title.trim(),
    deadline: newTask.deadline,        // 必须 YYYY-MM-DD
    brief: (newTask.brief ?? '').trim(),
    percent_contribution: newTask.percentContribution ?? 100,
    url: fileUrl,                      // 没有附件则为 null
  };

  try {
    // 3) 调后端创建
    // 期望返回 { success: true, data: { id: number } }
    const res = await apiService.adminCreateTask(selectedCourse.id, payload);
    if (!res?.success) throw new Error(res?.message || 'Create task failed');

    const newId = String(res.data.id);

    // 4) 更新本地状态
    const taskForUI = {
      id: newId,
      course_code: selectedCourse.id,
      title: payload.title,
      deadline: payload.deadline,
      brief: payload.brief,
      percentContribution: payload.percent_contribution,
      url: payload.url,
      createdAt: new Date().toISOString(),
    };

    const updated = [...tasks, taskForUI];
    setTasks(updated);
    updateTaskStatsLocal(selectedCourse.id, updated);
    // 5) 双写 localStorage
    const adminId = localStorage.getItem('current_user_id') || '';
    localStorage.setItem(
      `admin:${adminId}:course_tasks_${selectedCourse.id}`,
      JSON.stringify(updated)
    );
    const allKey = `admin:${adminId}:tasks`;
    const allRaw = localStorage.getItem(allKey);
    const allObj = allRaw ? JSON.parse(allRaw) : {};
    allObj[selectedCourse.id] = updated;
    localStorage.setItem(allKey, JSON.stringify(allObj));

    // 6) 关闭并重置
    handleCloseTaskModal();
  } catch (e: any) {
    console.error('Create task error:', e);
    alert(e?.message || 'Create task error');
  }
};

  // 编辑任务
  const handleEditTask = (task: any) => {
  setEditingTask(task);

  setNewTask({
    title: task.title || '',
    id: String(task.id || ''),
    deadline: task.deadline && task.deadline !== 'none' ? task.deadline : '',
    brief: task.brief || '', 
    attachment: null,  
    percentContribution: (
    task.percentContribution ??
    task.percent_contribution ??
    100
  ),
  });
  setUploadedUrl(task.url || null);
  setUploadStatus('idle');
  setUploadError(null);
  setTaskModalOpen(true);
};


  // 更新任务
  const handleUpdateTask = async () => {
  if (!editingTask || !selectedCourse) return;

  // 1) 基本校验
  if (!newTask.title?.trim()) { alert('Title is required'); return; }
  
  // 验证deadline格式: 支持 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM 或 YYYY-MM-DDTHH:MM:SS
  if (!newTask.deadline || !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$/.test(newTask.deadline)) {
    alert('Please select a valid deadline');
    return;
  }
  
  // 不允许选择过去日期（允许今天）
  const today = new Date();
  const todayStr = new Date(today.getFullYear(), today.getMonth(), today.getDate())
    .toISOString().slice(0, 10);
  const deadlineDate = newTask.deadline.slice(0, 10); // 提取日期部分
  if (deadlineDate < todayStr) {
    alert('Deadline 不能早于今天');
    return;
  }

  // 如果用户选择了新文件但还没上传完/上传失败，拦截
  if (newTask.attachment && uploadStatus !== 'done') {
    alert(uploadStatus === 'uploading' ? '附件仍在上传，请稍候…' : '附件上传失败，请重试');
    return;
  }

  try {
    // 2) 组装 payload（如果没换附件，就不传 url 字段，后端保持不变）
    const payload: any = {
      title: newTask.title.trim(),
      deadline: newTask.deadline,
      brief: (newTask.brief ?? '').trim(),
      percent_contribution: newTask.percentContribution ?? 100,
    };
    if (uploadedUrl) {
      payload.url = uploadedUrl;   // 仅当用户换了附件才覆盖
    }

    // 3) 调后端更新（下一步我们再在 apiService 里实现 adminEditTask）
    const hasNewFile = Boolean(uploadedUrl && uploadedUrl !== editingTask.url);
    const res = await apiService.adminEditTask(
      selectedCourse.id,
      editingTask.id,
      payload,
      { delete_old_file: hasNewFile }
    );
    if (!res?.success) throw new Error(res?.message || 'Update failed');

    // 4) 更新前端内存状态（UI字段名：percentContribution）
    const updatedTask = {
      ...editingTask,
      title: payload.title,
      deadline: payload.deadline,
      brief: payload.brief,
      percentContribution: payload.percent_contribution,
      url: uploadedUrl ?? editingTask.url ?? null,
      updatedAt: new Date().toISOString(),
    };
    const updatedList = tasks.map((t: any) =>
      String(t.id) === String(editingTask.id) ? updatedTask : t
    );
    setTasks(updatedList);

    // 5) 双写 localStorage（两处）
    const adminId = localStorage.getItem('current_user_id') || '';

    // 5.1 课程维度列表
    localStorage.setItem(
      `admin:${adminId}:course_tasks_${selectedCourse.id}`,
      JSON.stringify(updatedList)
    );

    // 5.2 汇总对象
    const allKey = `admin:${adminId}:tasks`;
    const allRaw = localStorage.getItem(allKey);
    const allObj = allRaw ? JSON.parse(allRaw) : {};
    const curList = Array.isArray(allObj[selectedCourse.id]) ? allObj[selectedCourse.id] : [];
    allObj[selectedCourse.id] = curList.map((t: any) =>
      String(t.id) === String(editingTask.id) ? updatedTask : t
    );
    localStorage.setItem(allKey, JSON.stringify(allObj));

    // 6) 收尾
    setEditingTask(null);
    resetUpload?.();             // 如果你有这个工具函数就调用；否则可忽略
    handleCloseTaskModal();
  } catch (e: any) {
    console.error('Update task error:', e);
    alert(e?.message || 'Update task error');
  }
};
  // 删除任务确认
  const handleDeleteTask = (taskId: string) => {
    setDeleteTaskId(taskId);
  };

  // 确认删除任务
  const handleConfirmDeleteTask = async () => {
  if (!deleteTaskId || !selectedCourse) return;

  try {
    // 1) 先调后端：删除数据库记录 + 删除 TaskProgress +（可选）删除附件文件
    const res = await apiService.adminDeleteTask(
      selectedCourse.id,
      deleteTaskId,
      { delete_file: true }     // 同时删除附件
    );

    if (!res?.success) {
      throw new Error(res?.message || 'Delete failed');
    }

    // 2) 成功后再更新本地状态
    const updatedTasks = tasks.filter((t: any) => String(t.id) !== String(deleteTaskId));
    setTasks(updatedTasks);
    updateTaskStatsLocal(selectedCourse.id, updatedTasks);
    // 3) 双写 localStorage
    const adminId = localStorage.getItem('current_user_id') || '';

    // 3.1 课程维度列表
    localStorage.setItem(
      `admin:${adminId}:course_tasks_${selectedCourse.id}`,
      JSON.stringify(updatedTasks)
    );

    // 3.2 汇总对象（按课程归档）
    const allKey = `admin:${adminId}:tasks`;
    const allRaw = localStorage.getItem(allKey);
    const allObj = allRaw ? JSON.parse(allRaw) : {};
    const curList = Array.isArray(allObj[selectedCourse.id]) ? allObj[selectedCourse.id] : [];
    allObj[selectedCourse.id] = curList.filter((t: any) => String(t.id) !== String(deleteTaskId));
    localStorage.setItem(allKey, JSON.stringify(allObj));

    // 4) 收尾
    setDeleteTaskId(null);
    // 可选：toast.success('Task deleted');
  } catch (e: any) {
    console.error('Delete task error:', e);
    alert(e?.message || 'Delete task error');
  }
};

  // 处理弹窗提交
  const handleTaskSubmit = editingTask ? handleUpdateTask : handleCreateTask;

  // 打开上传材料弹窗
  const handleUploadMaterial = () => {
    setMaterialModalOpen(true);
  };

  // 关闭上传材料弹窗
  const handleCloseMaterialModal = () => {
    setMaterialModalOpen(false);
    setNewMaterial({
      name: '',
      description: '',
      file: null
    });
    resetUpload();
  };

  // 处理材料表单输入
  const handleMaterialInputChange = (field: string, value: string | File | null) => {
  setNewMaterial(prev => ({ ...prev, [field]: value }));
};

  // 创建新材料
  const handleCreateMaterial = async () => {
  //console.log('file =', newMaterial.file, newMaterial.file instanceof File);
  const name = (newMaterial.name || '').trim();
  const description = (newMaterial.description || '').trim();
  const fileObj = newMaterial.file;

  if (!name) {
    alert(' Material  Name required');
    return;
  }
  if (!selectedCourse?.id) {
    alert('which course?');
    return;
  }
  if (!fileObj) {
    alert('choose your material!');
    return;
  }

  try {
    
    const fileUrl = await apiService.uploadMaterialFile(fileObj, selectedCourse.id);

    const courseId = String(selectedCourse.id);
    const createRes = await apiService.adminCreateMaterial(courseId, {
      title: name,
      description,
      url: fileUrl,
    });

    if (!createRes?.success) {
      throw new Error(createRes?.message || '创建失败');
    }

    const newId = String(createRes.data?.id ?? `M_${Date.now()}`);
    const adminId = localStorage.getItem('current_user_id') || '';

    // 更新本地状态
    const newItem = {
      id: newId,
      title: name,
      description,
      url: fileUrl,
    };
    const updatedMaterials = [...materials, newItem];
    setMaterials(updatedMaterials);

    //  同步 localStorage —— 单课
    const perCourseKey = `admin:${adminId}:course_materials_${courseId}`;
    localStorage.setItem(perCourseKey, JSON.stringify(updatedMaterials));

    // 同步 localStorage —— 汇总（Record<courseId, Material[]>）
    const allKey = `admin:${adminId}:materials`;
    let allMap: Record<string, any[]> = {};
    try {
      allMap = JSON.parse(localStorage.getItem(allKey) || '{}');
    } catch {
      allMap = {};
    }
    allMap[courseId] = updatedMaterials;
    localStorage.setItem(allKey, JSON.stringify(allMap));

    //  复位 & 关闭
    setNewMaterial({ name: '', description: '', file: null });
    setMaterialModalOpen(false);
    alert('Succeed!');
  } catch (err: any) {
    console.error('[handleCreateMaterial] failed:', err);
    alert(err?.message || 'Fail!');
  }
};

  // 编辑材料
  const handleEditMaterial = (material: any) => {
  setEditingMaterial(material);
  setNewMaterial({
    name: material.title ?? '',          
    description: material.description ?? '',
    file: null,                         
  });
  setMaterialModalOpen(true);
};

  // 更新材料
  const handleUpdateMaterial = async () => {
  const name = (newMaterial.name || '').trim();
  const description = (newMaterial.description || '').trim();
  const fileObj = newMaterial.file; // File | null

  if (!name || !editingMaterial?.id || !selectedCourse?.id) {
    alert('fail!');
    return;
  }

  const courseId = String(selectedCourse.id);
  const adminId = localStorage.getItem('current_user_id') || '';

  try {
    // 1) 如果用户上传了新文件：先上传拿到新 URL；若没上传则保留旧 URL
    let finalUrl: string = editingMaterial.url || '';
    if (fileObj instanceof File) {
      // 上传文件时把课程 id 一起传，后端会存到 material/<courseId>/ 下
      finalUrl = await apiService.uploadMaterialFile(fileObj, courseId);
    }

    // 2) 调用后端更新数据库（title/description，若换文件则同时更新 url）
    await apiService.adminUpdateMaterial(courseId, editingMaterial.id, {
      title: name,
      description,
      url: finalUrl, // 即使未更换文件也传原来的 url（后端幂等更新）
    });

    // 3) 刷新内存状态
    const updatedMaterials = materials.map((m) =>
      m.id === editingMaterial.id
        ? { ...m, title: name, description, url: finalUrl }
        : m
    );
    setMaterials(updatedMaterials);

    // 4) 同步 localStorage —— 单课
    const perCourseKey = `admin:${adminId}:course_materials_${courseId}`;
    localStorage.setItem(perCourseKey, JSON.stringify(updatedMaterials));

    // 5) 同步 localStorage —— 汇总（Record<courseId, Material[]>）
    const allKey = `admin:${adminId}:materials`;
    let allMap: Record<string, any[]> = {};
    try {
      allMap = JSON.parse(localStorage.getItem(allKey) || '{}');
    } catch {
      allMap = {};
    }
    allMap[courseId] = updatedMaterials;
    localStorage.setItem(allKey, JSON.stringify(allMap));

    // 6) 关闭并复位
    handleCloseMaterialModal();
    setEditingMaterial(null);
  } catch (err: any) {
    console.error('[handleUpdateMaterial] failed:', err);
    alert(err?.message || 'fail!');
  }
};

  // 删除材料
  const handleDeleteMaterial = (materialId: string) => {
    setDeleteMaterialId(materialId);
  };

  // 确认删除材料
  const handleConfirmDeleteMaterial = async () => {
  if (!deleteMaterialId || !selectedCourse?.id) return;

  const courseId = String(selectedCourse.id);
  const adminId = localStorage.getItem('current_user_id') || '';

  try {
    // 1) 先请求后端删除
    await apiService.adminDeleteMaterial(courseId, deleteMaterialId);

    // 2) 本地内存状态移除
    const updatedMaterials = materials.filter(m => m.id !== deleteMaterialId);
    setMaterials(updatedMaterials);

    // 3) 同步 localStorage —— 单课
    const perCourseKeyNew = `admin:${adminId}:course_materials_${courseId}`;
    localStorage.setItem(perCourseKeyNew, JSON.stringify(updatedMaterials));

    // 4) 同步 localStorage —— 汇总（Record<courseId, Material[]>）
    const allKey = `admin:${adminId}:materials`;
    let allMap: Record<string, any[]> = {};
    try {
      allMap = JSON.parse(localStorage.getItem(allKey) || '{}');
    } catch {
      allMap = {};
    }
    allMap[courseId] = updatedMaterials;
    localStorage.setItem(allKey, JSON.stringify(allMap));

    // 5) 关闭确认
    setDeleteMaterialId(null);
  } catch (err: any) {
    console.error('[handleConfirmDeleteMaterial] failed:', err);
    alert(err?.message || 'fail!');
  }
};

  // 根据是否在编辑模式决定提交函数
  const handleMaterialSubmit = editingMaterial ? handleUpdateMaterial : handleCreateMaterial;

  // Question相关处理函数
  const handleAddQuestion = () => {
    setEditingQuestion(null);
    setNewQuestion({
      type: 'multiple-choice',
      topic: '',
      title: '',
      description: '',
      keywords: '',
      questionText: '',
      options: ['', '', '', ''],
      correctAnswer: '',
      answer: '',
      sampleAnswer: '',
      keyPoints: '',
      score: 10,
      difficulty: 'Medium',
      gradingCriteria: '',
      hint: ''
    });
    setQuestionModalOpen(true);
  };

  const handleCloseQuestionModal = () => {
  setQuestionModalOpen(false);
  setEditingQuestion(null);
  setBatchQuestions([]); // 清空批量题目
  setCurrentQuestionIndex(0); // 重置索引
  setQuestionFileError(''); // 清空文件错误
  setNewQuestion((prev) => ({
    ...prev,
    topic: '',
    title: '',
    description: '',
    keywords: '',
    questionText: '',
    options: ['', '', '', ''],
    correctAnswer: '',
    answer: '',
    sampleAnswer: '',
    keyPoints: '',
    score: 10,
    difficulty: 'Medium',
    gradingCriteria: '',
    hint: ''
  }));
};

  // 清除已上传的文件内容，但不关闭弹窗
  const handleClearUploadedFile = () => {
    setBatchQuestions([]); // 清空批量题目列表
    setCurrentQuestionIndex(0); // 重置索引
    setQuestionFileError(''); // 清空错误信息
    setNewQuestion({
      type: newQuestion.type, // 保留题目类型
      topic: '',
      title: '',
      description: '',
      keywords: '',
      questionText: '',
      options: ['', '', '', ''],
      correctAnswer: '',
      answer: '',
      sampleAnswer: '',
      keyPoints: '',
      score: 10,
      difficulty: 'Medium',
      gradingCriteria: '',
      hint: ''
    });
    // 重置文件上传输入框
    const fileInput = document.getElementById('question-file-upload') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const handleQuestionInputChange = (field: string, value: any) => {
    setNewQuestion(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleOptionChange = (index: number, value: string) => {
    const newOptions = [...newQuestion.options];
    newOptions[index] = value;
    setNewQuestion(prev => ({
      ...prev,
      options: newOptions
    }));
  };

  // 处理文件上传并解析内容
  const handleQuestionFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 检查文件类型
    const validTypes = ['.txt', '.json'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!validTypes.includes(fileExtension)) {
      setQuestionFileError('Only .txt and .json files are supported');
      return;
    }

    setQuestionFileUploading(true);
    setQuestionFileError('');

    try {
      const text = await file.text();
      
      // 尝试解析文件内容
      if (fileExtension === '.json') {
        // JSON格式解析
        const data = JSON.parse(text);
        parseQuestionData(data);
      } else if (fileExtension === '.txt') {
        // TXT格式解析
        parseTextQuestionData(text);
      }
      
      setQuestionFileUploading(false);
    } catch (error) {
      console.error('File parsing error:', error);
      setQuestionFileError('Failed to parse file. Please check the file format.');
      setQuestionFileUploading(false);
    }

    // 清除文件输入
    event.target.value = '';
  };

  // 解析单个题目对象
  const parseQuestionObject = (data: any, currentType: string) => {
    // 智能判断题目类型：优先从数据本身判断，其次使用currentType
    let detectedType = currentType;
    
    // 如果数据中明确指定了type/qtype，使用数据中的类型
    if (data.type) {
      detectedType = data.type;
    } else if (data.qtype) {
      detectedType = data.qtype === 'mcq' ? 'multiple-choice' : 'short-answer';
    } 
    // 如果有options或correctAnswer字段，判断为选择题
    else if (data.options || data.correctAnswer || data.correct_answer) {
      detectedType = 'multiple-choice';
    } 
    // 如果有keyPoints或sampleAnswer字段，判断为简答题
    else if (data.keyPoints || data.key_points || data.sampleAnswer || data.sample_answer) {
      detectedType = 'short-answer';
    }
    
    return {
      type: detectedType,
      topic: data.topic || '',
      title: data.title || '',
      description: data.description || '',
      keywords: data.keywords || '',
      questionText: data.question || data.questionText || '',
      options: detectedType === 'multiple-choice' ? (data.options || ['', '', '', '']) : ['', '', '', ''],
      correctAnswer: detectedType === 'multiple-choice' ? (data.correctAnswer || data.correct_answer || '') : '',
      answer: '',
      sampleAnswer: detectedType === 'short-answer' ? (data.sampleAnswer || data.sample_answer || '') : '',
      keyPoints: detectedType === 'short-answer' ? (data.keyPoints || data.key_points || '') : '',
      score: data.score || 10,
      difficulty: data.difficulty || 'Medium',
      gradingCriteria: data.gradingCriteria || data.grading_criteria || '',
      hint: data.hint || ''
    };
  };

  // 解析JSON格式的题目数据（支持单个或批量）
  const parseQuestionData = (data: any) => {
    // 检查是否为批量题目（数组格式）
    if (Array.isArray(data)) {
      const parsedQuestions = data.map(item => parseQuestionObject(item, newQuestion.type));
      setBatchQuestions(parsedQuestions);
      setCurrentQuestionIndex(0);
      if (parsedQuestions.length > 0) {
        setNewQuestion(parsedQuestions[0]);
      }
    } else {
      // 单个题目
      const parsed = parseQuestionObject(data, newQuestion.type);
      setNewQuestion(parsed);
      setBatchQuestions([]);
    }
  };

  // 解析文本格式的题目数据（支持批量）
  const parseTextQuestionData = (text: string) => {
    // 检查是否包含分隔符 "---"，如果有则为批量题目
    const separator = '---';
    const hasSeparator = text.includes(separator);
    
    if (hasSeparator) {
      // 批量模式：按 "---" 分割多个题目
      const questionTexts = text.split(separator).map(q => q.trim()).filter(q => q);
      const parsedQuestions: any[] = [];
      
      questionTexts.forEach(questionText => {
        const lines = questionText.split('\n').map(line => line.trim()).filter(line => line);
        const data: any = {};
        
        lines.forEach(line => {
          // 支持 "字段名: 值" 或 "字段名=值" 格式
          const colonMatch = line.match(/^([^:]+):\s*(.+)$/);
          const equalMatch = line.match(/^([^=]+)=\s*(.+)$/);
          
          if (colonMatch) {
            const [, key, value] = colonMatch;
            assignFieldValue(data, key.trim().toLowerCase(), value.trim());
          } else if (equalMatch) {
            const [, key, value] = equalMatch;
            assignFieldValue(data, key.trim().toLowerCase(), value.trim());
          }
        });
        
        // 只添加有效的题目（至少有question字段）
        if (data.question) {
          parsedQuestions.push(parseQuestionObject(data, newQuestion.type));
        }
      });
      
      // 设置批量题目
      if (parsedQuestions.length > 0) {
        setBatchQuestions(parsedQuestions);
        setCurrentQuestionIndex(0);
        setNewQuestion(parsedQuestions[0]);
      }
    } else {
      // 单个题目模式
      const lines = text.split('\n').map(line => line.trim()).filter(line => line);
      const data: any = {};

      lines.forEach(line => {
        // 支持 "字段名: 值" 或 "字段名=值" 格式
        const colonMatch = line.match(/^([^:]+):\s*(.+)$/);
        const equalMatch = line.match(/^([^=]+)=\s*(.+)$/);
        
        if (colonMatch) {
          const [, key, value] = colonMatch;
          assignFieldValue(data, key.trim().toLowerCase(), value.trim());
        } else if (equalMatch) {
          const [, key, value] = equalMatch;
          assignFieldValue(data, key.trim().toLowerCase(), value.trim());
        }
      });

      parseQuestionData(data);
    }
  };

  // 根据字段名分配值
  const assignFieldValue = (data: any, key: string, value: string) => {
    if (key.includes('topic') || key.includes('主题')) {
      data.topic = value;
    } else if (key.includes('question') && !key.includes('sample') || key.includes('题目')) {
      data.question = value;
    } else if (key.includes('option') || key.includes('选项')) {
      if (!data.options) data.options = ['', '', '', ''];
      
      // 方式1: 从字段名中提取选项标签 (Option A, Option B, 选项A, 选项B)
      const keyMatch = key.match(/([A-Da-d1-4])/);
      if (keyMatch) {
        const label = keyMatch[1];
        const index = label.match(/[A-Da-d]/) 
          ? label.toUpperCase().charCodeAt(0) - 65 
          : parseInt(label) - 1;
        if (index >= 0 && index < 4) {
          data.options[index] = value;
        }
      } else {
        // 方式2: 从值中提取选项标签 (A: content, A) content)
        const valueMatch = value.match(/^([A-Da-d1-4])[\s:)]+(.+)$/);
        if (valueMatch) {
          const [, label, content] = valueMatch;
          const index = label.match(/[A-Da-d]/) 
            ? label.toUpperCase().charCodeAt(0) - 65 
            : parseInt(label) - 1;
          if (index >= 0 && index < 4) {
            data.options[index] = content;
          }
        }
      }
    } else if (key.includes('correct') || key.includes('正确答案')) {
      data.correctAnswer = value.toUpperCase().charAt(0);
    } else if (key.includes('sample') && key.includes('answer') || key.includes('示例答案')) {
      data.sampleAnswer = value;
    } else if (key.includes('key') && key.includes('point') || key.includes('关键要点')) {
      data.keyPoints = value;
    } else if (key.includes('score') || key.includes('分数')) {
      data.score = parseInt(value) || 10;
    } else if (key.includes('difficulty') || key.includes('难度')) {
      data.difficulty = value;
    } else if (key.includes('grading') || key.includes('评分标准')) {
      data.gradingCriteria = value;
    } else if (key.includes('hint') || key.includes('提示')) {
      data.hint = value;
    }
  };

//创建题目
  const handleCreateQuestion = async () => {
  // 验证必填字段
  if (!newQuestion.topic.trim() || !newQuestion.questionText.trim() || !newQuestion.gradingCriteria.trim()) {
    alert('Please fill in all required fields (Topic, Question, Grading Criteria).');
    return;
  }
  
  // 验证选择题特定字段
  if (newQuestion.type === 'multiple-choice' && !newQuestion.correctAnswer) {
    alert('Please select the correct answer for multiple choice question.');
    return;
  }
  
  // 验证简答题特定字段
  if (newQuestion.type === 'short-answer' && (!newQuestion.sampleAnswer.trim() || !newQuestion.keyPoints.trim())) {
    alert('Please fill in Sample Answer and Key Points for short answer question.');
    return;
  }
  
  if (!selectedCourse) {
    alert('No course selected.');
    return;
  }

  const adminId = localStorage.getItem('current_user_id') || '';
  const courseId = selectedCourse.id;

  // 1) 先构造本地"临时题目"，立即更新 UI
  const tempId = `q_${Date.now()}`;
  const newQuestionItem = {
    id: tempId,
    type: newQuestion.type,
    topic: newQuestion.topic,
    title: newQuestion.title,
    description: newQuestion.description,
    keywords: newQuestion.keywords,
    questionText: newQuestion.questionText,
    options: newQuestion.type === 'multiple-choice' ? newQuestion.options : [],
    correctAnswer:
      newQuestion.type === 'multiple-choice'
        ? newQuestion.correctAnswer
        : newQuestion.sampleAnswer,
    sampleAnswer: newQuestion.sampleAnswer,
    keyPoints: newQuestion.keyPoints,
    score: newQuestion.score,
    difficulty: newQuestion.difficulty,
    gradingCriteria: newQuestion.gradingCriteria,
    hint: newQuestion.hint,
    createdAt: new Date().toISOString(),
  };

  const optimistic = [...questions, newQuestionItem];
  setQuestions(optimistic);
  if (adminId) {
    const courseKey = `admin:${adminId}:course_questions_${courseId}`;
    const globalKey = `admin:${adminId}:questions`;

  // 更新当前课程缓存
  localStorage.setItem(courseKey, JSON.stringify(optimistic));

  //  更新全局 questions 索引
  try {
    const allStr = localStorage.getItem(globalKey);
    const all = allStr ? JSON.parse(allStr) : {};

    // 确保是对象
    if (typeof all !== 'object' || Array.isArray(all)) {
      console.warn('[fix localStorage] resetting invalid global structure');
      localStorage.setItem(globalKey, JSON.stringify({ [courseId]: optimistic }));
    } else {
      all[courseId] = optimistic;
      localStorage.setItem(globalKey, JSON.stringify(all));
    }
  } catch (err) {
    console.error('[localStorage] parse failed', err);
    localStorage.setItem(globalKey, JSON.stringify({ [courseId]: optimistic }));
  }
  }

  // 2) 组装后端 payload
  const labels = ['A', 'B', 'C', 'D'] as const;
  const keywordsArr = newQuestion.keywords
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  const payload: Omit<ApiQuestion, 'id'> & {
    topic?: string;
    sampleAnswer?: string;
    keyPoints?: string;
    score?: number;
    difficulty?: string;
    gradingCriteria?: string;
    hint?: string;
  } =
  newQuestion.type === 'multiple-choice'
    ? {
        qtype: 'mcq',
        title: newQuestion.title || newQuestion.topic,
        description: newQuestion.description || '',
        text: newQuestion.questionText,
        keywords: keywordsArr,
        choices: (newQuestion.options || []).map((content, idx) => ({
          label: labels[idx],
          order: idx,
          content,
          isCorrect: labels[idx] === newQuestion.correctAnswer,  
        })),
        topic: newQuestion.topic,
        score: newQuestion.score,
        difficulty: newQuestion.difficulty,
        gradingCriteria: newQuestion.gradingCriteria,
        hint: newQuestion.hint,
      }
    : {
        qtype: 'short',
        title: newQuestion.title || newQuestion.topic,
        description: newQuestion.description || '',
        text: newQuestion.questionText,
        keywords: keywordsArr,
        answer: newQuestion.sampleAnswer,
        topic: newQuestion.topic,
        sampleAnswer: newQuestion.sampleAnswer,
        keyPoints: newQuestion.keyPoints,
        score: newQuestion.score,
        difficulty: newQuestion.difficulty,
        gradingCriteria: newQuestion.gradingCriteria,
        hint: newQuestion.hint,
      };

  // 3) 调后端创建；成功后用真实 id 替换临时 id；失败则回滚本地
  try {
   
    const res = await apiService.adminCreateCourseQuestion(courseId, payload) ; // { id }
    console.log("[create question] response =", res);
    const realId = String(res.id);

    const withRealId = optimistic.map(q =>
      q.id === tempId ? { ...q, id: realId } : q
    );
    setQuestions(withRealId);
    if (adminId) {
      localStorage.setItem(
        `admin:${adminId}:course_questions_${courseId}`,
        JSON.stringify(withRealId)
      );
    }
    handleCloseQuestionModal();
  } catch (err) {
    console.error('[create question] failed:', err);
    // 回滚：移除刚才插入的临时题目
    const rolledBack = questions; // 原始列表
    setQuestions(rolledBack);
    if (adminId) {
      localStorage.setItem(
        `admin:${adminId}:course_questions_${courseId}`,
        JSON.stringify(rolledBack)
      );
    }
    alert('Create question failed.');
  } finally {
  }
};

// 批量创建题目
const handleBatchCreateQuestions = async () => {
  if (!selectedCourse || batchQuestions.length === 0) {
    alert('No questions to create.');
    return;
  }

  // 保存当前编辑的题目到批量列表
  const updatedBatch = [...batchQuestions];
  updatedBatch[currentQuestionIndex] = newQuestion;

  const adminId = localStorage.getItem('current_user_id') || '';
  const courseId = selectedCourse.id;
  const labels = ['A', 'B', 'C', 'D'] as const;

  let successCount = 0;
  let failCount = 0;
  const createdQuestions: any[] = []; // 收集成功创建的题目

  for (let i = 0; i < updatedBatch.length; i++) {
    const question = updatedBatch[i];
    
    // 验证必填字段
    if (!question.topic.trim() || !question.questionText.trim() || !question.gradingCriteria.trim()) {
      console.warn(`Question ${i + 1} is missing required fields, skipping...`);
      failCount++;
      continue;
    }

    if (question.type === 'multiple-choice' && !question.correctAnswer) {
      console.warn(`Question ${i + 1} (MCQ) is missing correct answer, skipping...`);
      failCount++;
      continue;
    }

    if (question.type === 'short-answer' && (!question.sampleAnswer.trim() || !question.keyPoints.trim())) {
      console.warn(`Question ${i + 1} (Short Answer) is missing sample answer or key points, skipping...`);
      failCount++;
      continue;
    }

    try {
      const keywordsArr = (question.keywords || '')
        .split(',')
        .map((s: string) => s.trim())
        .filter(Boolean);

      const payload: any = question.type === 'multiple-choice'
        ? {
            qtype: 'mcq',
            title: question.title || question.topic,
            description: question.description || '',
            text: question.questionText,
            keywords: keywordsArr,
            choices: (question.options || []).map((content: string, idx: number) => ({
              label: labels[idx],
              order: idx,
              content,
              isCorrect: labels[idx] === question.correctAnswer,
            })),
            topic: question.topic,
            score: question.score,
            difficulty: question.difficulty,
            gradingCriteria: question.gradingCriteria,
            hint: question.hint,
          }
        : {
            qtype: 'short',
            title: question.title || question.topic,
            description: question.description || '',
            text: question.questionText,
            keywords: keywordsArr,
            answer: question.sampleAnswer,
            topic: question.topic,
            sampleAnswer: question.sampleAnswer,
            keyPoints: question.keyPoints,
            score: question.score,
            difficulty: question.difficulty,
            gradingCriteria: question.gradingCriteria,
            hint: question.hint,
          };

      const res = await apiService.adminCreateCourseQuestion(courseId, payload);
      const realId = String(res.id);

      // 添加到收集列表
      const newQuestionItem = {
        id: realId,
        ...question,
        createdAt: new Date().toISOString(),
      };

      createdQuestions.push(newQuestionItem);
      successCount++;
    } catch (err) {
      console.error(`Failed to create question ${i + 1}:`, err);
      failCount++;
    }
  }

  // 一次性更新所有题目到状态和localStorage
  if (successCount > 0) {
    const updatedQuestions = [...questions, ...createdQuestions];
    setQuestions(updatedQuestions);

    if (adminId) {
      const courseKey = `admin:${adminId}:course_questions_${courseId}`;
      const globalKey = `admin:${adminId}:questions`;

      localStorage.setItem(courseKey, JSON.stringify(updatedQuestions));

      try {
        const allStr = localStorage.getItem(globalKey);
        const all = allStr ? JSON.parse(allStr) : {};
        all[courseId] = updatedQuestions;
        localStorage.setItem(globalKey, JSON.stringify(all));
      } catch (err) {
        console.error('[localStorage] update failed', err);
      }
    }
  }

  alert(`Batch creation completed!\nSuccess: ${successCount}\nFailed: ${failCount}`);
  handleCloseQuestionModal();
};

 // 编辑题目
  const handleEditQuestion = (q: any) => {
  if (!q) return;

  // 你在 handleCreateQuestion 里也用到了这套 labels，保持一致
  const labels = ['A', 'B', 'C', 'D'] as const;

  // 1) 题型归一化：前端是 'multiple-choice' | 'short-answer'；后端是 'mcq' | 'short'
  const type: 'multiple-choice' | 'short-answer' =
    q.type
      ? q.type
      : (q.qtype === 'mcq' ? 'multiple-choice' : 'short-answer');

  // 2) 文本字段兜底
  const title = q.title ?? '';
  const description = q.description ?? '';
  const questionText = q.questionText ?? q.text ?? '';

  // 3) keywords 统一成「逗号分隔字符串」
  let keywords = '';
  if (Array.isArray(q.keywords)) {
    keywords = q.keywords.filter(Boolean).join(', ');
  } else if (typeof q.keywords === 'string') {
    keywords = q.keywords;
  } else {
    keywords = '';
  }

  // 4) options / correctAnswer / answer 归一化
  let options: string[] = ['', '', '', ''];
  let correctAnswer: string = '';
  let answer: string = '';

  if (type === 'multiple-choice') {
    // options 既可能是 string[]（你本地的），也可能是后端的 choices[{content,isCorrect}]
    if (Array.isArray(q.options)) {
      options = q.options.map((x: any) => String(x ?? '')).slice(0, 4);
    } else if (Array.isArray(q.choices)) {
      options = q.choices.map((c: any) => String(c?.content ?? '')).slice(0, 4);
      // 从后端结构推断正确选项
      const idx = q.choices.findIndex((c: any) => c?.isCorrect === true);
      if (idx >= 0 && idx < labels.length) {
        correctAnswer = labels[idx];
      }
    }

    // 如果源里已经有 correctAnswer（你乐观写入过），直接兜底覆盖
    if (typeof q.correctAnswer === 'string' && labels.includes(q.correctAnswer)) {
      correctAnswer = q.correctAnswer;
    }

    // 补齐到 4 个
    while (options.length < 4) options.push('');
  } else {
    // 简答题：优先用 q.answer；没有就兜底 q.correctAnswer（你本地乐观结构会把简答放在 correctAnswer）
    answer = (q.answer ?? q.correctAnswer ?? '') as string;
  }

  // 5) 写入编辑态 + 打开弹窗
  setEditingQuestion(q);
  setNewQuestion({
    type,
    topic: q.topic || '',
    title,
    description,
    keywords,
    questionText,
    options,
    correctAnswer, // 仅 MCQ 用；简答题为空串即可
    answer,        // 仅简答题用；MCQ 为空串即可
    sampleAnswer: q.sampleAnswer || '',
    keyPoints: q.keyPoints || '',
    score: q.score || 10,
    difficulty: q.difficulty || 'Medium',
    gradingCriteria: q.gradingCriteria || '',
    hint: q.hint || ''
  });
  setQuestionModalOpen(true);
};
 // 然后更新题目
  const handleUpdateQuestion = async () => {
  if (!editingQuestion) return;
  
  // 验证必填字段
  if (!newQuestion.topic.trim() || !newQuestion.questionText.trim() || !newQuestion.gradingCriteria.trim()) {
    alert('Please fill in all required fields (Topic, Question, Grading Criteria).');
    return;
  }
  
  // 验证选择题特定字段
  if (newQuestion.type === 'multiple-choice') {
    if (!newQuestion.correctAnswer) { 
      alert('Please select a correct option.'); 
      return; 
    }
  } else {
    // 验证简答题特定字段
    if (!newQuestion.sampleAnswer.trim() || !newQuestion.keyPoints.trim()) { 
      alert('Please fill in Sample Answer and Key Points for short answer question.'); 
      return; 
    }
  }
  
  if (!selectedCourse) {
    alert('No course selected.');
    return;
  }

  const courseId   = selectedCourse.id;
  const questionId = String(editingQuestion.id);
  const adminId = localStorage.getItem('current_user_id') || '';
  const courseKey = `admin:${adminId}:course_questions_${courseId}`;
  const globalKey = `admin:${adminId}:questions`;
   

 const updatedOne = {
  ...editingQuestion,
  type: newQuestion.type,
  topic: newQuestion.topic,
  title: newQuestion.title,
  description: newQuestion.description,
  keywords: newQuestion.keywords,
  questionText: newQuestion.questionText,
  options: newQuestion.type === 'multiple-choice' ? newQuestion.options : [],
  correctAnswer: newQuestion.type === 'multiple-choice' ? newQuestion.correctAnswer : '',
  answer: newQuestion.type === 'short-answer' ? newQuestion.sampleAnswer : '',
  sampleAnswer: newQuestion.sampleAnswer,
  keyPoints: newQuestion.keyPoints,
  score: newQuestion.score,
  difficulty: newQuestion.difficulty,
  gradingCriteria: newQuestion.gradingCriteria,
  hint: newQuestion.hint,
  updatedAt: new Date().toISOString(),
};

// 2️⃣ 做乐观更新（更新前端显示和 localStorage）
// const prevQuestions = questions; // 用于失败回滚
const optimistic = questions.map(q =>
  String(q.id) === questionId ? updatedOne : q
);
setQuestions(optimistic);

// 3️⃣ 写入当前课程缓存
if (adminId) {
  try {
    localStorage.setItem(courseKey, JSON.stringify(optimistic));
  } catch (e) {
    console.warn('[localStorage] failed to write courseKey', e);
  }

  // 4️⃣ 更新全局 questions 索引
  try {
    const allStr = localStorage.getItem(globalKey);
    const all = allStr ? JSON.parse(allStr) : {};

    if (typeof all !== 'object' || Array.isArray(all)) {
      console.warn('[fix localStorage] resetting invalid global structure');
      localStorage.setItem(globalKey, JSON.stringify({ [courseId]: optimistic }));
    } else {
      all[courseId] = optimistic;
      localStorage.setItem(globalKey, JSON.stringify(all));
    }
  } catch (err) {
    console.error('[localStorage] parse failed', err);
    try {
      localStorage.setItem(globalKey, JSON.stringify({ [courseId]: optimistic }));
    } catch {}
  }
}
  
  //这里跟create一样
  const labels = ['A', 'B', 'C', 'D'] as const;
  const keywordsArr = (newQuestion.keywords || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  const payload: Omit<ApiQuestion, 'id'> & {
    topic?: string;
    sampleAnswer?: string;
    keyPoints?: string;
    score?: number;
    difficulty?: string;
    gradingCriteria?: string;
    hint?: string;
  } =
    newQuestion.type === 'multiple-choice'
      ? {
          qtype: 'mcq',
          title: newQuestion.title || newQuestion.topic, // 使用topic作为title的后备
          description: newQuestion.description || '',
          text: newQuestion.questionText,
          keywords: keywordsArr,
          choices: (newQuestion.options || []).map((content, idx) => ({
            label: labels[idx],
            order: idx,
            content,
            isCorrect: labels[idx] === newQuestion.correctAnswer,
          })),
          topic: newQuestion.topic,
          score: newQuestion.score,
          difficulty: newQuestion.difficulty,
          gradingCriteria: newQuestion.gradingCriteria,
          hint: newQuestion.hint,
        }
      : {
          qtype: 'short',
          title: newQuestion.title || newQuestion.topic,
          description: newQuestion.description || '',
          text: newQuestion.questionText,
          keywords: keywordsArr,
          answer: newQuestion.sampleAnswer,
          topic: newQuestion.topic,
          sampleAnswer: newQuestion.sampleAnswer,
          keyPoints: newQuestion.keyPoints,
          score: newQuestion.score,
          difficulty: newQuestion.difficulty,
          gradingCriteria: newQuestion.gradingCriteria,
          hint: newQuestion.hint,
        };

  try {
    console.log('[update payload]', payload);

  // 这里接住返回值
    const res = await apiService.adminUpdateCourseQuestion(courseId, questionId, payload);
    console.log('[update response]', res);
    if (!res || res.success === false) {

    throw new Error(res?.message || 'Update failed');
  }
    setQuestions(prev =>
      prev.map(q =>
        String(q.id) === questionId
          ? {
              ...q,
              type: newQuestion.type,
              topic: newQuestion.topic,
              title: newQuestion.title,
              description: newQuestion.description,
              keywords: newQuestion.keywords,
              questionText: newQuestion.questionText,
              options: newQuestion.type === 'multiple-choice' ? [...(newQuestion.options || [])] : [],
              correctAnswer: newQuestion.type === 'multiple-choice' ? newQuestion.correctAnswer : '',
              answer: newQuestion.type === 'short-answer' ? newQuestion.sampleAnswer : '',
              sampleAnswer: newQuestion.sampleAnswer,
              keyPoints: newQuestion.keyPoints,
              score: newQuestion.score,
              difficulty: newQuestion.difficulty,
              gradingCriteria: newQuestion.gradingCriteria,
              hint: newQuestion.hint,
              updatedAt: new Date().toISOString(),
            }
          : q
      )
    );

    // 成功后收尾
    handleCloseQuestionModal();
  } catch (err) {
    console.error('[update question] failed:', err);
    alert('Update question failed.');
  }
};

  // 删除题目
  const handleDeleteQuestion = async (questionId: number | string) => {
  if (!selectedCourse) return alert('No course selected.');
  if (!window.confirm('Are you sure you want to delete this question?')) return;

  const courseId = selectedCourse.id;
  const adminId = localStorage.getItem('current_user_id') || '';

  try {
    //  调后端删除
    const res = await apiService.adminDeleteCourseQuestion(courseId, String(questionId));
    if (!res.success) {
      alert(res.message || 'Delete failed.');
      return;
    }

    // 前端内存更新
    const updated = questions.filter(q => String(q.id) !== String(questionId));
    setQuestions(updated);

    //  同步到 localStorage
    const courseKey = `admin:${adminId}:course_questions_${courseId}`;
    const globalKey = `admin:${adminId}:questions`;

    localStorage.setItem(courseKey, JSON.stringify(updated));

    try {
      const allStr = localStorage.getItem(globalKey);
      const all = allStr ? JSON.parse(allStr) : {};
      if (typeof all === 'object' && !Array.isArray(all)) {
        all[courseId] = updated;
        localStorage.setItem(globalKey, JSON.stringify(all));
      }
    } catch {
      localStorage.setItem(globalKey, JSON.stringify({ [courseId]: updated }));
    }

    alert('Question deleted successfully.');
  } catch (err) {
    console.error('[delete question] failed:', err);
    alert('Failed to delete question.');
  }
  };

  // 批量删除题目
  const handleBatchDelete = async () => {
    if (!selectedCourse) return alert('No course selected.');
    if (selectedQuestions.length === 0) return alert('Please select questions to delete.');
    
    const confirmMsg = `Are you sure you want to delete ${selectedQuestions.length} question(s)?`;
    if (!window.confirm(confirmMsg)) return;

    const courseId = selectedCourse.id;
    const adminId = localStorage.getItem('current_user_id') || '';

    let successCount = 0;
    let failCount = 0;

    for (const questionId of selectedQuestions) {
      try {
        const res = await apiService.adminDeleteCourseQuestion(courseId, String(questionId));
        if (res.success) {
          successCount++;
        } else {
          failCount++;
        }
      } catch (err) {
        console.error(`Failed to delete question ${questionId}:`, err);
        failCount++;
      }
    }

    // 更新前端状态
    const updated = questions.filter(q => !selectedQuestions.includes(String(q.id)));
    setQuestions(updated);

    // 同步到 localStorage
    const courseKey = `admin:${adminId}:course_questions_${courseId}`;
    const globalKey = `admin:${adminId}:questions`;

    localStorage.setItem(courseKey, JSON.stringify(updated));

    try {
      const allStr = localStorage.getItem(globalKey);
      const all = allStr ? JSON.parse(allStr) : {};
      if (typeof all === 'object' && !Array.isArray(all)) {
        all[courseId] = updated;
        localStorage.setItem(globalKey, JSON.stringify(all));
      }
    } catch {
      localStorage.setItem(globalKey, JSON.stringify({ [courseId]: updated }));
    }

    // 重置批量删除状态
    setSelectedQuestions([]);
    setBatchDeleteMode(false);

    alert(`Batch delete completed!\nSuccess: ${successCount}\nFailed: ${failCount}`);
  };

  // 切换批量删除模式
  const toggleBatchDeleteMode = () => {
    setBatchDeleteMode(!batchDeleteMode);
    setSelectedQuestions([]);
  };

  // 切换题目选中状态
  const toggleQuestionSelection = (questionId: string) => {
    setSelectedQuestions(prev => 
      prev.includes(questionId) 
        ? prev.filter(id => id !== questionId)
        : [...prev, questionId]
    );
  };

  // 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedQuestions.length === questions.length) {
      setSelectedQuestions([]);
    } else {
      setSelectedQuestions(questions.map(q => String(q.id)));
    }
  };

  // 获取课程图片索引 - 使用课程创建时保存的索引
  const getCourseIllustrationIndex = (courseId: string) => {
    if (!courseId) return 0;
    
    // 从localStorage加载课程数据，获取保存的illustrationIndex
    try {
      const savedCourses = localStorage.getItem('admin_created_courses');
      if (savedCourses) {
        const courses = JSON.parse(savedCourses);
        const course = courses.find((c: any) => c.id === courseId);
        if (course && course.illustrationIndex !== undefined) {
          return course.illustrationIndex;
        }
      }
    } catch (error) {
      console.error('Error loading course illustration index:', error);
    }
    
    // 如果找不到保存的索引，使用默认的哈希计算作为后备
    let hash = 0;
    for (let i = 0; i < courseId.length; i++) {
      hash = ((hash << 5) - hash) + courseId.charCodeAt(i);
      hash = hash & hash;
    }
    return Math.abs(hash) % adminIllustrations.length;
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="admin-manage-course-layout">
      {/* 左侧导航栏 - 严格按照Figma设计 */}
      <aside className="amc-sidebar">
        {/* 用户信息卡片 */}
        <div className="amc-profile-card">
          <div className="avatar">
            <img
              src={user?.avatarUrl || AvatarIcon}
              width={48}
              height={48}
              alt="avatar"
              style={{ borderRadius: '50%', objectFit: 'cover' }}
              onError={(e) => { (e.currentTarget as HTMLImageElement).src = AvatarIcon; }}
            />
          </div>
          <div className="info">
            <div className="name">{user?.name || 'Admin'}</div>
            <div className="email">{user?.email || 'admin@example.com'}</div>
          </div>
          <button className="chevron" aria-label="Open profile" onClick={() => (window.location.hash = '#/admin-profile')}>
            <img src={ArrowRight} width={16} height={16} alt="" />
          </button>
        </div>

        {/* 导航菜单 */}
        <nav className="amc-nav">
          <a className="item" href="#/admin-home">
            <img src={IconHome} className="nav-icon" alt="" /> Home
          </a>
          <a className="item active" href="#/admin-courses">
            <img src={IconCourses} className="nav-icon" alt="" /> My Courses
          </a>
          <a className="item" href="#/admin-monitor">
            <img src={IconMonitor} className="nav-icon" alt="" /> Analytics
          </a>
        </nav>

        {/* 插画区域 */}
        <div className="amc-illustration">
          <img src={adminHomepageImage} alt="Admin Dashboard" style={{ width: '100%', height: 'auto', borderRadius: '20px' }} />
        </div>

        {/* 登出按钮 */}
        <button className="btn-outline" onClick={() => setLogoutModalOpen(true)}>Log Out</button>
      </aside>

      {/* 右侧主内容区域 - 严格按照Figma设计 */}
      <main className="amc-main">
        {/* 课程详情卡片 - 严格按照Figma设计 */}
        <div className="course-detail-card">
          {selectedCourse ? (
            <div className="course-content">
              {/* 课程头部：只保留这一份 */}
              <div className="cd-hero-clean">
                <button
                  className="back-circle"
                  aria-label="Back to courses"
                  onClick={() => (window.location.hash = '#/admin-courses')}
                >
                  <img src={ArrowRight} width={16} height={16} alt="" className="chev-left" />
                </button>

                <div className="course-meta-row">
                  <div className="course-image-section">
                    <div className="image-container">
                      <img
                        src={adminIllustrations[getCourseIllustrationIndex(selectedCourse.id)]}
                        alt={selectedCourse.title}
                        className="course-image"
                      />
                      <button className="image-edit-btn">+</button>
                    </div>
                  </div>

                  <div className="course-info-section">
                    <div className="course-id">{selectedCourse.id}</div>
                    <h1 className="course-title">{selectedCourse.title}</h1>
                    <p className="course-description">
                      {selectedCourse.description || 'No description provided'}
                    </p>
                  </div>
                </div>
              </div>

              {/* 灰卡内部只在这里滚动 */}
              <div className="amc-detail-content">
                <div className="function-sections">
                  {/* Task List */}
                  <div className="function-section">
                    <div className="section-header">
                      <h3 className="section-title">Task List</h3>
                      <button className="add-btn" onClick={handleAddTask}>+ Add Task</button>
                    </div>
                    <div className={`section-content ${tasks.length === 0 ? 'empty' : ''}`}>
                      {tasks.length > 0 ? (
                        <div className="task-list">
                          {tasks.map((task) => (
                            <div key={task.id} className="task-item">
                              <div className="task-info">
                                <h4 className="task-title">{task.title}</h4>
                                <p className="task-brief">{task.brief}</p>
                                <div className="task-meta">
                                  <span className="meta-chip">Task Proportion: {task.percentContribution}%</span>
                                  <span className="meta-chip">Deadline: {task.deadline}</span>
                                </div>
                                {task.attachment && (
                                  <div className="task-attachment">
                                    <span className="attachment-label">Attachment:</span>
                                    <span className="attachment-file">{task.attachment}</span>
                                  </div>
                                )}
                              </div>
                              <div className="task-actions">
                                <button 
                                  className="edit-btn" 
                                  onClick={() => handleEditTask(task)}
                                >
                                  Edit
                                </button>
                                <button 
                                  className="delete-btn" 
                                  onClick={() => handleDeleteTask(task.id)}
                                >
                                  Delete
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="empty-state">
                          <span className="empty-text">No tasks added yet</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Learning Material */}
                  <div className="function-section">
                    <div className="section-header">
                      <h3 className="section-title">Learning Material</h3>
                      <button className="add-btn" onClick={handleUploadMaterial}>+ Upload Material</button>
                    </div>
                    <div className={`section-content ${materials.length === 0 ? 'empty' : ''}`}>
                      {materials.length > 0 ? (
                        <div className="material-list">
                          {materials.map((material) => (
                            <div key={material.id} className="material-item">
                              <div className="material-info">
                                <h4 className="material-title">{material.name}</h4>
                                <p className="material-description">{material.description}</p>
                                {material.file && (
                                  <div className="material-attachment">
                                    <span className="attachment-label">File:</span>
                                    <span className="attachment-file">{material.file}</span>
                                  </div>
                                )}
                              </div>
                              <div className="material-actions">
                                <button 
                                  className="edit-btn" 
                                  onClick={() => handleEditMaterial(material)}
                                >
                                  Edit
                                </button>
                                <button 
                                  className="delete-btn" 
                                  onClick={() => handleDeleteMaterial(material.id)}
                                >
                                  Delete
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="empty-state">
                          <span className="empty-text">No materials uploaded yet</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Question Bank */}
                  <div className="function-section">
                    <div className="section-header">
                      <h3 className="section-title">Question Bank</h3>
                      <div style={{display: 'flex', gap: '8px'}}>
                        {batchDeleteMode && questions.length > 0 && (
                          <>
                            <button 
                              className="batch-delete-btn" 
                              onClick={toggleSelectAll}
                              style={{background: selectedQuestions.length === questions.length ? '#BB87AC' : '#fff', color: selectedQuestions.length === questions.length ? '#fff' : '#BB87AC'}}
                            >
                              {selectedQuestions.length === questions.length ? '✓ Deselect All' : 'Select All'}
                            </button>
                            <button 
                              className="batch-delete-btn delete" 
                              onClick={handleBatchDelete}
                              disabled={selectedQuestions.length === 0}
                            >
                              Delete ({selectedQuestions.length})
                            </button>
                          </>
                        )}
                        <button 
                          className={`add-btn ${batchDeleteMode ? 'cancel' : ''}`} 
                          onClick={toggleBatchDeleteMode}
                        >
                          {batchDeleteMode ? 'Cancel' : 'Batch Delete'}
                        </button>
                        <button className="add-btn" onClick={handleAddQuestion}>+ Add Question</button>
                      </div>
                    </div>
                    <div className={`section-content ${questions.length === 0 ? 'empty' : ''}`}>
                      {questions.length > 0 ? (
                        <div className="question-list">
                          {questions.map((question) => (
                            <div key={question.id} className="question-item">
                              {batchDeleteMode && (
                                <div className="question-checkbox">
                                  <input
                                    type="checkbox"
                                    checked={selectedQuestions.includes(String(question.id))}
                                    onChange={() => toggleQuestionSelection(String(question.id))}
                                  />
                                </div>
                              )}
                              <div className="question-info">
                                <h4 className="question-title">{question.topic || question.title || 'Untitled Question'}</h4>
                                <p className="question-description">{question.questionText || question.description || 'No description'}</p>
                                <div className="question-meta">
                                  <span className="meta-chip">Type: {question.type === 'multiple-choice' ? 'Multiple Choice' : 'Short Answer'}</span>
                                  {question.type === 'multiple-choice' ? (
                                    <span className="meta-chip">
                                      Correct Answer: {question.correctAnswer || 'Not set'}
                                      {question.correctAnswer && question.options && question.options.length > 0 && (() => {
                                        const answerIndex = ['A', 'B', 'C', 'D'].indexOf(question.correctAnswer);
                                        const answerText = answerIndex >= 0 ? question.options[answerIndex] : '';
                                        return answerText ? ` - ${answerText}` : '';
                                      })()}
                                    </span>
                                  ) : (
                                    <span className="meta-chip">Key Points: {question.keywords || question.keyPoints || 'No key points'}</span>
                                  )}
                                </div>
                              </div>
                              {!batchDeleteMode && (
                                <div className="question-actions">
                                  <button 
                                    className="edit-btn" 
                                    onClick={() => handleEditQuestion(question)}
                                  >
                                    Edit
                                  </button>
                                  <button 
                                    className="delete-btn" 
                                    onClick={() => handleDeleteQuestion(question.id)}
                                  >
                                    Delete
                                  </button>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="empty-state">
                          <span className="empty-text">No questions added yet</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="no-course-selected">
              <h2>No Course Selected</h2>
              <p>Please select a course from the My Courses page to manage it.</p>
              <button 
                className="browse-courses-btn" 
                onClick={() => handleNavigation('#/admin-courses')}
              >
                Browse Courses
              </button>
            </div>
          )}
        </div>
      </main>

      {/* 创建任务弹窗 */}
      {taskModalOpen && (
        <div className="task-modal-overlay">
          <div className="task-modal">
            {/* 弹窗头部 */}
            <div className="task-modal-header">
              <h2 className="task-modal-title">
                {editingTask ? 'Edit Task' : 'Create New Task'}
              </h2>
              <button 
                className="task-modal-close" 
                onClick={handleCloseTaskModal}
                aria-label="Close"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11 14L5 8L11 2" stroke="#161616" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="task-modal-content">
              {/* Task Title */}
              <div className="task-input-group">
                <label className="task-label">Task Title: <span className="required">*</span></label>
                <input
                  type="text"
                  className="task-input"
                  value={newTask.title}
                  onChange={(e) => handleTaskInputChange('title', e.target.value)}
                  placeholder="Enter task title"
                />
                {!newTask.title.trim() && (
                  <span className="task-error">Title is required</span>
                )}
              </div>

              <div className="task-input-group">
                <label className="task-label">Percentage (%): <span className="required">*</span></label>
                <input
                  type="number"
                  className="task-input"
                  min={1}
                  max={100}
                  step={1}
                  value={newTask.percentContribution}
                  onChange={(e) => {
                    const num = Number(e.target.value);
                    handleTaskInputChange('percentContribution', num);
                  }}
                />
              </div>

              {/* Task ID */}
              <div className="task-input-group">
                <label className="task-label">Task ID:</label>
                <input
                  type="text"
                  className="task-input"
                  value={newTask.id}
                  onChange={(e) => handleTaskInputChange('id', e.target.value)}
                  placeholder="Enter task ID"
                />
              </div>

              {/* Task Deadline */}
              <div className="task-input-group">
                <label className="task-label">Task Deadline (Optional):</label>
                <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                  <input
                    type="datetime-local"
                    className="task-input"
                    value={newTask.deadline}
                    min={new Date().toISOString().slice(0, 16)} 
                    onChange={(e) => handleTaskInputChange('deadline', e.target.value)}
                    lang="en-US"
                    title="Select deadline date and time (YYYY-MM-DD HH:MM:SS format)"
                    step="1"
                    style={{flex: 1}}
                  />
                  <span style={{fontSize: '12px', color: '#6D6D78', whiteSpace: 'nowrap'}}>
                    YYYY-MM-DD HH:MM:SS
                  </span>
                </div>
                <div style={{fontSize: '12px', color: '#6D6D78', marginTop: '4px'}}>
                  If no deadline selected, it will be set to "none"
                </div>
              </div>

              {/* Brief */}
              <div className="task-input-group">
                <label className="task-label">Brief:</label>
                <input
                  type="text"
                  className="task-input"
                  value={newTask.brief}
                  onChange={(e) => handleTaskInputChange('brief', e.target.value)}
                  placeholder="Enter brief description"
                />
              </div>

              {/* Attach Detail Doc */}
              <div className="task-input-group">
              <label className="task-label">Attach Detail Doc</label>
              <div className="file-upload-area">
                <div className="file-upload-icon">📎</div>
                <span className="file-upload-text">Upload Files</span>
                <input
                        key={fileInputKey}    
                        type="file"
                        className="file-input"
                        onChange={async (e) => {
                          const file = e.target.files?.[0] || null;
                          handleTaskInputChange('attachment', file); // 存 File 对象

                          if (!file || !selectedCourse){
                            setUploadStatus('idle');
                            setUploadedUrl(null);
                            setUploadError(null);
                            return;  // 没选文件或没选课程直接返回
                          }

                          try {
                            setUploadStatus('uploading');  // 上传中
                            setUploadError(null);
                            const fd = new FormData();
                            fd.append('file', file);
                            fd.append('course', selectedCourse.id);

                           
                            const token = localStorage.getItem('auth_token') || '';

                            const res = await fetch('/api/courses_admin/upload/task-file', {
                              method: 'POST',
                              headers: token ? { Authorization: `Bearer ${token}` } : {},
                              body: fd,
                            }).then(r => r.json());

                            if (!res?.success) {
                              setUploadStatus('error');
                              setUploadError(res?.message || 'fail!');
                              setUploadedUrl(null);
                              return;
                            }

                            // 上传成功
                            setUploadedUrl(res.data.url as string);   // 存入 /task/... 路径
                            setUploadStatus('done');
                          } catch (err: any) {
                            setUploadStatus('error');
                            setUploadError(err?.message || 'error!');
                            setUploadedUrl(null);
                          }
                        }}
                      />
                      {uploadStatus === 'uploading' && <div className="hint">Uploading...</div>}
                      {uploadStatus === 'done' && <div className="hint ok">Done✓</div>}
                      {uploadStatus === 'error' && <div className="hint err">{uploadError || 'fail!'}</div>}
                </div>
              </div>
            </div>

            {/* 弹窗底部 */}
            <div className="task-modal-footer">
              <button 
                className="task-create-btn" 
                onClick={handleTaskSubmit}
                disabled={!newTask.title.trim()}
              >
                {editingTask ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 上传材料弹窗 */}
      {materialModalOpen && (
        <div className="material-modal-overlay">
          <div className="material-modal">
            {/* 弹窗头部 */}
            <div className="material-modal-header">
              <h2 className="material-modal-title">{editingMaterial ? 'Edit Material' : 'New Material'}</h2>
              <button 
                className="material-modal-close" 
                onClick={handleCloseMaterialModal}
                aria-label="Close"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11 14L5 8L11 2" stroke="#161616" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="material-modal-content">
              {/* Material Name */}
              <div className="material-input-group">
                <label className="material-label">Material Name: <span className="required">*</span></label>
                <input
                  type="text"
                  className="material-input"
                  value={newMaterial.name}
                  onChange={(e) => handleMaterialInputChange('name', e.target.value)}
                  placeholder="Enter material name"
                />
                {!newMaterial.name.trim() && (
                  <span className="material-error">Material name is required</span>
                )}
              </div>

              {/* Description */}
              <div className="material-input-group">
                <label className="material-label">Description:</label>
                <textarea
                  className="material-textarea"
                  value={newMaterial.description}
                  onChange={(e) => handleMaterialInputChange('description', e.target.value)}
                  placeholder="Enter material description"
                  rows={3}
                />
              </div>

              {/* Upload File */}
              <div className="material-input-group">
                <label className="material-label">Upload File:</label>
                <div className="material-file-upload-area">
                  <div className="material-file-upload-icon">📎</div>
                  <span className="material-file-upload-text">Upload Files</span>
                  <input
                      key={fileInputKey}
                      type="file"
                      className="material-file-input"
                      onChange={async (e) => {
                        const file = e.target.files?.[0] || null;

                      
                        handleMaterialInputChange('file', file);

                        
                        if (!file || !selectedCourse) {
                          setUploadStatus('idle');
                          setUploadedUrl(null);
                          setUploadError(null);
                          return;
                        }

                        try {
                          setUploadStatus('uploading');
                          setUploadError(null);

                          const fd = new FormData();
                          fd.append('file', file);                      // 字段名必须是 file
                          fd.append('course', String(selectedCourse.id)); // 用课程ID分目录

                          const token = localStorage.getItem('auth_token') || '';

                          const resp = await fetch('/api/courses_admin/upload/material-file', {
                            method: 'POST',
                            headers: token ? { Authorization: `Bearer ${token}` } : {},
                            body: fd,
                          });

                          const res = await resp.json().catch(() => ({}));

                          if (!resp.ok || !res?.success || !res?.data?.url) {
                            setUploadStatus('error');
                            setUploadError(res?.message || `HTTP ${resp.status}`);
                            setUploadedUrl(null);
                            return;
                          }

                          // 上传成功：拿到 /material/<courseId>/<filename>
                          setUploadedUrl(res.data.url as string);
                          setUploadStatus('done');
                        } catch (err: any) {
                          setUploadStatus('error');
                          setUploadError(err?.message || 'Upload failed');
                          setUploadedUrl(null);
                        }
                      }}
                    />


                    {uploadStatus === 'uploading' && <div className="hint">Uploading...</div>}
                    {uploadStatus === 'done' && <div className="hint ok">Done✓</div>}
                    {uploadStatus === 'error' && <div className="hint err">{uploadError || 'fail!'}</div>}
                </div>
              </div>
            </div>

            {/* 弹窗底部 */}
            <div className="material-modal-footer">
              <button 
                className="material-create-btn" 
                onClick={handleMaterialSubmit}
                disabled={!newMaterial.name.trim()}
              >
                {editingMaterial ? 'Update' : 'Add'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 删除任务确认弹窗 */}
      <ConfirmationModal
        isOpen={deleteTaskId !== null}
        onClose={() => setDeleteTaskId(null)}
        onConfirm={handleConfirmDeleteTask}
        title="Delete Task"
        message="Are you sure you want to delete this task? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
      />

      {/* 删除材料确认弹窗 */}
      <ConfirmationModal
        isOpen={deleteMaterialId !== null}
        onClose={() => setDeleteMaterialId(null)}
        onConfirm={handleConfirmDeleteMaterial}
        title="Delete Material"
        message="Are you sure you want to delete this material? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
      />

      {/* 创建题目弹窗 */}
      {questionModalOpen && (
        <div className="question-modal-overlay">
          <div className="question-modal">
            {/* 弹窗头部 */}
            <div className="question-modal-header">
              <h2 className="question-modal-title">
                {editingQuestion ? 'Edit Question' : 
                 batchQuestions.length > 0 ? 
                   `Batch Upload - Question ${currentQuestionIndex + 1} of ${batchQuestions.length}` : 
                   'Create New Question'}
              </h2>
              {batchQuestions.length > 0 && (
                <div className="batch-navigation">
                  <button
                    className="batch-nav-btn"
                    onClick={() => {
                      if (currentQuestionIndex > 0) {
                        // 保存当前修改
                        const updated = [...batchQuestions];
                        updated[currentQuestionIndex] = newQuestion;
                        setBatchQuestions(updated);
                        // 切换到上一个
                        setCurrentQuestionIndex(currentQuestionIndex - 1);
                        setNewQuestion(updated[currentQuestionIndex - 1]);
                      }
                    }}
                    disabled={currentQuestionIndex === 0}
                  >
                    ← Previous
                  </button>
                  <span className="batch-indicator">
                    {currentQuestionIndex + 1} / {batchQuestions.length}
                  </span>
                  <button
                    className="batch-nav-btn"
                    onClick={() => {
                      if (currentQuestionIndex < batchQuestions.length - 1) {
                        // 保存当前修改
                        const updated = [...batchQuestions];
                        updated[currentQuestionIndex] = newQuestion;
                        setBatchQuestions(updated);
                        // 切换到下一个
                        setCurrentQuestionIndex(currentQuestionIndex + 1);
                        setNewQuestion(updated[currentQuestionIndex + 1]);
                      }
                    }}
                    disabled={currentQuestionIndex === batchQuestions.length - 1}
                  >
                    Next →
                  </button>
                </div>
              )}
              <button 
                className="question-modal-close" 
                onClick={handleCloseQuestionModal}
                aria-label="Close"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11 14L5 8L11 2" stroke="#161616" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="question-modal-content">
              {/* 题目类型选择 */}
              <div className="question-input-group">
                <label className="question-label">Question Type: <span className="required">*</span></label>
                <div className="question-type-selector">
                  <div 
                    className={`type-option ${newQuestion.type === 'multiple-choice' ? 'selected' : ''}`}
                    onClick={() => handleQuestionInputChange('type', 'multiple-choice')}
                  >
                    Multiple Choice
                  </div>
                  <div 
                    className={`type-option ${newQuestion.type === 'short-answer' ? 'selected' : ''}`}
                    onClick={() => handleQuestionInputChange('type', 'short-answer')}
                  >
                    Short Answer
                  </div>
                </div>
              </div>

              {/* 文件上传区 */}
              <div className="question-file-upload-section">
                <div className="upload-header">
                  <span className="upload-icon">📁</span>
                  <span className="upload-title">Quick Fill from File (Supports Batch Upload)</span>
                </div>
                <div className="upload-description">
                  Upload a .txt or .json file to auto-fill the form. 
                  <strong> Use "---" to separate multiple questions in TXT files, or upload JSON array for batch creation.</strong>
                </div>
                <div className="upload-input-wrapper">
                  <input
                    type="file"
                    id="question-file-upload"
                    accept=".txt,.json"
                    onChange={handleQuestionFileUpload}
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="question-file-upload" className="upload-button">
                    {questionFileUploading ? 'Processing...' : 'Choose File'}
                  </label>
                  {questionFileError && (
                    <span className="upload-error">{questionFileError}</span>
                  )}
                </div>
                <details className="upload-format-guide">
                  <summary>📖 File Format Guide</summary>
                  <div className="format-content">
                    <p><strong>✨ Batch Upload Support:</strong></p>
                    <div className="format-note batch-note">
                      Upload multiple questions at once! Use <strong>"---"</strong> to separate questions in TXT files, or upload a JSON array.
                    </div>
                    
                    <p><strong>Single Question - TXT Format:</strong></p>
                    <pre className="format-example">
Topic: Data Structures
Question: What is a stack?
Score: 10
Difficulty: Medium
Grading Criteria: Must explain LIFO concept
Hint: Think about plates

For Multiple Choice:
Option A: A FIFO structure
Option B: A LIFO structure
Option C: A tree structure
Option D: A graph structure
Correct Answer: B

For Short Answer:
Sample Answer: A stack is a LIFO data structure
Key Points: LIFO, push, pop, top element
                    </pre>
                    
                    <p><strong>Multiple Questions - TXT Format (use "---" separator):</strong></p>
                    <pre className="format-example">
Topic: Database Fundamentals
Question: What is a primary key?
Option A: First column
Option B: Unique identifier
Option C: Foreign key
Option D: Index key
Correct Answer: B
Score: 10
Difficulty: Easy
Grading Criteria: Must identify unique identifier
Hint: Think about uniqueness

---

Topic: SQL Queries
Question: Which clause filters grouped results?
Option A: WHERE
Option B: HAVING
Option C: FILTER
Option D: GROUP BY
Correct Answer: B
Score: 15
Difficulty: Medium
Grading Criteria: Understand WHERE vs HAVING
Hint: One filters before, one after grouping
                    </pre>

                    <p><strong>Batch Upload - JSON Array Format:</strong></p>
                    <pre className="format-example">
[
  {'{'}
    "topic": "Data Structures",
    "question": "What is a stack?",
    "options": ["FIFO structure", "LIFO structure", "Tree", "Graph"],
    "correctAnswer": "B",
    "score": 10,
    "difficulty": "Medium",
    "gradingCriteria": "Must explain LIFO",
    "hint": "Think about plates"
  {'}'},
  {'{'}
    "topic": "Algorithms",
    "question": "What is Big O notation?",
    "sampleAnswer": "Describes algorithm complexity",
    "keyPoints": "Time complexity, space complexity",
    "score": 20,
    "difficulty": "Hard",
    "gradingCriteria": "Define notation and explain purpose",
    "hint": "Focus on growth rate"
  {'}'}
]
                    </pre>
                    
                    <p><strong>📥 Download Sample Files:</strong></p>
                    <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap'}}>
                      <a href="/sample-batch-mcq.txt" download className="sample-link">📄 MCQ Batch (TXT)</a>
                      <a href="/sample-batch-short.txt" download className="sample-link">📄 Short Answer Batch (TXT)</a>
                      <a href="/sample-batch-mcq.json" download className="sample-link">📄 MCQ Batch (JSON)</a>
                      <a href="/sample-batch-short.json" download className="sample-link">📄 Short Answer Batch (JSON)</a>
                    </div>
                  </div>
                </details>
              </div>

              {/* 主题 */}
              <div className="question-input-group">
                <label className="question-label">Topic: <span className="required">*</span></label>
                <input
                  type="text"
                  className="question-input"
                  value={newQuestion.topic}
                  onChange={(e) => handleQuestionInputChange('topic', e.target.value)}
                  placeholder="Enter topic (e.g., Introduction to Programming)"
                />
                {!newQuestion.topic.trim() && (
                  <span className="question-error">Topic is required</span>
                )}
              </div>

              {/* 题目 */}
              <div className="question-input-group">
                <label className="question-label">Question: <span className="required">*</span></label>
                <textarea
                  className="question-textarea"
                  value={newQuestion.questionText}
                  onChange={(e) => handleQuestionInputChange('questionText', e.target.value)}
                  placeholder="Enter the question text"
                  rows={3}
                />
                {!newQuestion.questionText.trim() && (
                  <span className="question-error">Question text is required</span>
                )}
              </div>

              {/* 选择题选项 */}
              {newQuestion.type === 'multiple-choice' && (
                <>
                  <div className="question-input-group">
                    <label className="question-label">Options: <span className="required">*</span></label>
                    {newQuestion.options.map((option, index) => (
                      <div key={index} className="option-input-group">
                        <span className="option-label">{String.fromCharCode(65 + index)}:</span>
                        <input
                          type="text"
                          className="option-input"
                          value={option}
                          onChange={(e) => handleOptionChange(index, e.target.value)}
                          placeholder={`Enter option ${String.fromCharCode(65 + index)}`}
                        />
                      </div>
                    ))}
                  </div>

                  {/* 正确答案选择 */}
                  <div className="question-input-group">
                    <label className="question-label">Correct Answer: <span className="required">*</span></label>
                    <select
                      className="question-input"
                      value={newQuestion.correctAnswer}
                      onChange={(e) => handleQuestionInputChange('correctAnswer', e.target.value)}
                    >
                      <option value="">Select correct option</option>
                      {newQuestion.options.map((option, index) => (
                        option.trim() && (
                          <option key={index} value={String.fromCharCode(65 + index)}>
                            {String.fromCharCode(65 + index)}: {option}
                          </option>
                        )
                      ))}
                    </select>
                    {!newQuestion.correctAnswer && (
                      <span className="question-error">Please select the correct answer</span>
                    )}
                  </div>
                </>
              )}

              {/* 简答题字段 */}
              {newQuestion.type === 'short-answer' && (
                <>
                  {/* 示例答案 */}
                  <div className="question-input-group">
                    <label className="question-label">Sample Answer: <span className="required">*</span></label>
                    <textarea
                      className="question-textarea"
                      value={newQuestion.sampleAnswer}
                      onChange={(e) => handleQuestionInputChange('sampleAnswer', e.target.value)}
                      placeholder="Enter a sample answer"
                      rows={3}
                    />
                    {!newQuestion.sampleAnswer.trim() && (
                      <span className="question-error">Sample answer is required</span>
                    )}
                  </div>

                  {/* 关键要点 */}
                  <div className="question-input-group">
                    <label className="question-label">Key Points: <span className="required">*</span></label>
                    <textarea
                      className="question-textarea"
                      value={newQuestion.keyPoints}
                      onChange={(e) => handleQuestionInputChange('keyPoints', e.target.value)}
                      placeholder="Enter key points (comma separated, e.g., LIFO, push operation, pop operation)"
                      rows={2}
                    />
                    {!newQuestion.keyPoints.trim() && (
                      <span className="question-error">Key points are required</span>
                    )}
                  </div>
                </>
              )}

              {/* 分数 */}
              <div className="question-input-group">
                <label className="question-label">Score:</label>
                <input
                  type="number"
                  className="question-input"
                  value={newQuestion.score}
                  onChange={(e) => handleQuestionInputChange('score', parseInt(e.target.value) || 0)}
                  placeholder="Enter score"
                  min="1"
                  max="100"
                />
              </div>

              {/* 难度 */}
              <div className="question-input-group">
                <label className="question-label">Difficulty: <span className="required">*</span></label>
                <select
                  className="question-input"
                  value={newQuestion.difficulty}
                  onChange={(e) => handleQuestionInputChange('difficulty', e.target.value)}
                >
                  <option value="Easy">Easy</option>
                  <option value="Medium">Medium</option>
                  <option value="Hard">Hard</option>
                </select>
              </div>

              {/* 评分标准 */}
              <div className="question-input-group">
                <label className="question-label">Grading Criteria: <span className="required">*</span></label>
                <textarea
                  className="question-textarea"
                  value={newQuestion.gradingCriteria}
                  onChange={(e) => handleQuestionInputChange('gradingCriteria', e.target.value)}
                  placeholder="Enter grading criteria (e.g., Exact match required, Must include key concepts)"
                  rows={2}
                />
                {!newQuestion.gradingCriteria.trim() && (
                  <span className="question-error">Grading criteria is required</span>
                )}
              </div>

              {/* 提示 */}
              <div className="question-input-group">
                <label className="question-label">Hint:</label>
                <textarea
                  className="question-textarea"
                  value={newQuestion.hint}
                  onChange={(e) => handleQuestionInputChange('hint', e.target.value)}
                  placeholder="Enter a hint (optional)"
                  rows={2}
                />
              </div>
            </div>

            {/* 弹窗底部 */}
            <div className="question-modal-footer">
              {batchQuestions.length > 0 ? (
                <>
                  <button 
                    className="question-create-btn batch-create-btn" 
                    onClick={handleBatchCreateQuestions}
                  >
                    Create All {batchQuestions.length} Questions
                  </button>
                  <button 
                    className="question-cancel-btn" 
                    onClick={handleClearUploadedFile}
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button 
                  className="question-create-btn" 
                  onClick={() => {
                    if (editingQuestion) {
                      handleUpdateQuestion();   
                    } else {
                      handleCreateQuestion();  
                    }
                  }}
                  disabled={
                    !newQuestion.topic.trim() || 
                    !newQuestion.questionText.trim() || 
                    !newQuestion.gradingCriteria.trim() ||
                    (newQuestion.type === 'multiple-choice' && !newQuestion.correctAnswer) ||
                    (newQuestion.type === 'short-answer' && (!newQuestion.sampleAnswer.trim() || !newQuestion.keyPoints.trim()))
                  }
                >
                  {editingQuestion ? 'Update' : 'Create'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      <ConfirmationModal
        isOpen={logoutModalOpen}
        onClose={() => setLogoutModalOpen(false)}
        onConfirm={handleLogout}
        title="Log Out"
        message="Are you sure you want to log out?"
        confirmText="Log Out"
        cancelText="Cancel"
      />

      <style>{css}</style>
      <style>{cssHotfix}</style>
    </div>
  );
}

/* HOTFIX：让 AdminManageCourse 的左侧栏与 AdminCourses 完全一致 */
const cssHotfix = `
/* === HOTFIX：让 AdminManageCourse 的左侧栏与 AdminCourses 完全一致 === */

/* 统一外层 grid：侧栏 280px、gap 48px、padding 32px（与第一页一致） */
.admin-manage-course-layout{
  grid-template-columns: 280px 1fr;
  gap: 48px;
  padding: 32px;
  color: var(--amc-text);
  background: #fff;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  min-height: 100vh;
}

/* 导航项与图标尺寸对齐第一页 */
.amc-nav .item { font-size: 14px; }
.amc-nav .nav-icon { width: 20px; height: 20px; }

/* 激活态（My Courses 高亮）使用第一页的紫底与深色文字 + 20px 圆角 */
.amc-nav .item.active{
  background: #BB87AC;    /* 等同第一页 --ac-primary */
  color: #172239;
  font-weight: 600;
  border-radius: 20px;
}

/* 退出按钮改为描边按钮（不要固定 333×63），与第一页一致 */
.btn-outline{
  width: auto;
  height: auto;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid #EAEAEA; /* 等同第一页边框色 */
  background: #fff;
  color: #172239;
  font-size: 14px;
  font-weight: 600;
}

/* 取消 1440px 媒体查询里把侧栏固定定位的行为，恢复与第一页相同的 grid 流式布局 */
@media (max-width: 1440px){
  .amc-sidebar{ position: static; }
  .amc-main{ left: auto; width: auto; height: auto; }
}
`;

/* Admin Manage Course 页面样式 - 严格按照Figma设计 */
const css = `
:root{
  --amc-border: #EAEAEA;
  --amc-muted: #6D6D78;
  --amc-text: #172239;
  --amc-card-bg: #FFFFFF;
  --amc-shadow: 0 8px 24px rgba(0,0,0,0.04);
  --amc-primary: #BB87AC; /* 管理员紫色主题 */
  --amc-primary-light: rgba(187, 135, 172, 0.49); /* 半透明紫色 */
}

.admin-manage-course-layout{
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 48px;
  padding: 32px;
  color: var(--amc-text);
  background: #fff;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  font-size: 16px;
  height: 100vh; /* 修改：固定高度，不随内容拉伸 */
  overflow: hidden; /* 防止整个页面滚动 */
}

/* 左侧导航栏 - 与AdminCourses页面完全一致 */
.amc-sidebar{
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
}

/* 用户信息卡片 */
.amc-profile-card{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--amc-border);
  border-radius: 20px;
  background: var(--amc-card-bg);
  box-shadow: var(--amc-shadow);
  height: 95.36px;
}

.amc-profile-card .avatar{
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  background: #F4F6FA;
  display: grid;
  place-items: center;
}

.amc-profile-card .info{
  flex: 1;
}

.amc-profile-card .info .name{
  color: var(--amc-text);
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.amc-profile-card .info .email{
  color: var(--amc-muted);
  font-size: 12px;
  font-weight: 400;
}

.amc-profile-card .chevron{
  background: #fff;
  border: 1px solid var(--amc-border);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.amc-profile-card .chevron:hover{
  background: var(--amc-primary-light);
  cursor: pointer;
}

/* 导航菜单 */
.amc-nav{
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--amc-border);
  border-radius: 20px;
  background: #fff;
  box-shadow: var(--amc-shadow);
}

/* 导航菜单 */
.amc-nav .item{
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 12px;
  text-decoration: none;
  color: var(--amc-muted);
  font-weight: 500;
}

.amc-nav .item.active{
  background: var(--amc-primary);
  color: #172239;
  font-weight: 600;
  border-radius: 20px;
}

.amc-nav .nav-icon{
  width: 20px;
  height: 20px;
}

/* 统一 Manage 页插图区域为与 Courses 页一致 */
.amc-illustration{
  margin-top: auto;
  margin-bottom: 20px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.amc-illustration img{
  width: 100%;
  height: auto;
  border-radius: 20px;
  display: block;
}



/* 右侧整体：不滚（把滚动交给灰卡片内部） */
.amc-main{
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 100%;
  overflow: hidden;            /* 关键：右侧整体不滚 */
}

/* —— 统一为与第一页一致的数值 —— */

/* 菜单项字号：16px（第一页是 16px） */
.amc-nav .item{
  font-size: 16px !important;
}

/* 图标尺寸：20×20（第一页是 20×20） */
.amc-nav .nav-icon{
  width: 20px !important;
  height: 20px !important;
}

/* 容器基准字号锁定，避免继承波动 */
.admin-manage-course-layout{
  font-size: 16px !important;             /* 和第一页保持一致 */
  grid-template-columns: 280px 1fr !important;  /* 侧栏宽一致 */
}

/* 白色大卡片本身：充满高度，不滚 */
.course-detail-card{
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;               /* 允许子项收缩 */
  overflow: hidden;            /* 不在这里滚 */
  width: 100%;
  background: #fff;
  border-radius: 48px;
  border: 1px solid var(--amc-border);
  padding: 40px;
  margin-top: 0; /* 与左侧用户信息上方对齐 */
}

/* 返回按钮样式 - 参考学生端设计 */
.cd-hero-clean{
  position: relative;
  text-align: left;
  padding: 4px 0 8px;
  margin-bottom: 6px;
  background: transparent;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.back-circle{
  padding: 8px;
  border: 1px solid var(--amc-border);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  align-self: flex-start;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.chev-left{
  transform: rotate(180deg);
}

.course-meta-row{
  display: flex;
  align-items: flex-start;
  gap: 32px;
  flex: 1;
}

/* 课程基本信息 */
.course-basic-info{
  display: flex;
  align-items: flex-start;
  gap: 32px;
  margin-bottom: 40px;
}

.course-image-section{
  position: relative;
}

.image-container{
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  align-items: flex-start; /* 图片顶部对齐 */
}

.course-image{
  width: 100%;
  height: 100%;
  object-fit: contain; /* 改为contain以完整显示图片，不裁剪 */
}

/* 隐藏图片编辑按钮 */
.image-edit-btn{
  display: none;
}

.course-info-section{
  flex: 1;
}

/* Course ID：使用学生端CourseDetail的标题大小 */
.course-id{
  font-size: 28px;
  font-weight: 800;
  color: var(--amc-text);
  margin-bottom: 8px;
  letter-spacing: .2px;
}

/* Course Title：与Course Description使用相同的字体大小 */
.course-title{
  font-size: 16px;
  color: var(--amc-muted);
  font-weight: 500;
  margin: 0 0 16px 0;
}

.course-description{
  font-size: 16px;
  color: var(--amc-muted);
  line-height: 1.6;
  margin: 0;
}

/* 三个纵向排列的功能框 */
.function-sections{
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.function-section{
  border: none;
  border-radius: 16px;
  padding: 24px;
  background: #f8f9fa;
  border-left: 4px solid #BB87AC;
  box-sizing: border-box; /* 确保padding和border包含在元素尺寸内 */
}

.section-header{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title{
  font-size: 18px;
  font-weight: 600;
  color: var(--amc-text);
  margin: 0;
}

.add-btn{
  padding: 8px 16px;
  background: var(--amc-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.add-btn:hover{
  background: #a5769a;
}

/* 空状态样式 */
.section-content.empty{
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 0;
  border: none;
}

.section-content:not(.empty) {
  min-height: 120px;
}

.empty-state{
  text-align: center;
}

.empty-text{
  color: var(--amc-muted);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.2; /* 避免不同字体回退带来的抖动 */
}

/* Task列表样式 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 统一空状态在三块里的位置与高度 */
.function-section .section-content {
  min-height: 120px; /* 保证三个框高度一致；需要更高就一起改这个值 */
}

.function-section .section-content.empty {
  display: grid;         /* grid + place-items 最简单的完全居中 */
  place-items: center;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border: none;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: transform 0.2s ease;
}

.task-item:hover {
  transform: translateY(-2px);
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--amc-text);
  margin: 0 0 8px 0;
}

.task-brief {
  font-size: 14px;
  color: var(--amc-muted);
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.task-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.meta-chip {
  font-size: 12px;
  color: #6D6D78;
  background: #F8F8FA;
  border: 1px solid #EFEFF2;
  padding: 4px 8px;
  border-radius: 999px;
  font-weight: 500;
}

.task-attachment {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--amc-muted);
}

.attachment-label {
  font-weight: 500;
}

.attachment-file {
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.task-actions {
  display: flex;
  gap: 8px;
}

.edit-btn, .delete-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.edit-btn {
  background: var(--amc-primary);
  color: white;
}

.edit-btn:hover {
  background: #BB87AC;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.delete-btn:hover {
  background: #c82333;
}

/* Material列表样式 */
.material-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.material-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border: none;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: transform 0.2s ease;
}

.material-item:hover {
  transform: translateY(-2px);
}

/* Question Bank列表样式 */
.question-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border: none;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: transform 0.2s ease;
  gap: 12px;
}

.question-item:hover {
  transform: translateY(-2px);
}

/* 批量删除复选框 */
.question-checkbox {
  display: flex;
  align-items: flex-start;
  padding-top: 4px;
}

.question-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #BB87AC;
}

/* 批量删除按钮样式 */
.batch-delete-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #BB87AC;
  background: #fff;
  color: #BB87AC;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Montserrat', sans-serif;
}

.batch-delete-btn:hover {
  background: #F5EFFF;
}

.batch-delete-btn.delete {
  background: #E31B54;
  color: #fff;
  border-color: #E31B54;
}

.batch-delete-btn.delete:hover {
  background: #C01747;
}

.batch-delete-btn.delete:disabled {
  background: #D0D5DD;
  border-color: #D0D5DD;
  cursor: not-allowed;
  opacity: 0.6;
}

.add-btn.cancel {
  background: #fff;
  color: #6D6D78;
  border: 1px solid #D0D5DD;
}

.add-btn.cancel:hover {
  background: #F5F5F5;
}

.material-info {
  flex: 1;
}

.material-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--amc-text);
  margin: 0 0 8px 0;
}

.material-description {
  font-size: 14px;
  color: var(--amc-muted);
  margin: 0 0 12px 0;
  line-height: 1.4;
}

/* Question Bank 专用样式 */
.question-info {
  flex: 1;
  margin: 0;
  padding: 0;
}

.question-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--amc-text);
  margin: 0 0 6px 0;
  line-height: 1.3;
}

.question-description {
  font-size: 14px;
  color: var(--amc-muted);
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.question-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 0;
}

.material-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.material-attachment {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.material-actions {
  display: flex;
  gap: 8px;
}

.question-actions {
  display: flex;
  gap: 8px;
}

/* 无课程选中状态 */
.no-course-selected{
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  text-align: center;
}

.no-course-selected h2{
  font-size: 24px;
  font-weight: 600;
  color: var(--amc-text);
  margin-bottom: 16px;
}

.no-course-selected p{
  font-size: 16px;
  color: var(--amc-muted);
  margin-bottom: 32px;
}

.browse-courses-btn{
  padding: 12px 24px;
  background: var(--amc-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

/* 中间层：一定要能"吃到高度"，把剩余空间让给滚动层 */
.course-content{
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;               /* 没这句就不触发滚动 */
}

/* 只在这里滚动（学生端同款） */
.amc-detail-content{
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;               /* 关键 */
  overflow-y: auto;            /* 只这里出现滚动条 */
  overflow-x: hidden;
  gap: 24px;
  padding-right: 12px;         /* 给滚动条留点空隙 */
}

/* （可选）美化滚动条，仅作用于灰卡片内部 */
.amc-detail-content{
  scrollbar-width: thin;
  scrollbar-color: rgba(23,34,57,0.25) transparent;
}
.amc-detail-content::-webkit-scrollbar{ width:8px; }
.amc-detail-content::-webkit-scrollbar-track{ background: transparent; }
.amc-detail-content::-webkit-scrollbar-thumb{
  background: rgba(23,34,57,0.25);
  border-radius: 8px;
  border: 2px solid transparent;
  background-clip: content-box;
}
.amc-detail-content:hover::-webkit-scrollbar-thumb{
  background: rgba(23,34,57,0.35);
}

/* 响应式设计 - 与 Courses 页完全一致 */
@media (max-width: 1440px){
  /* 若要与 Courses 页一致，可改回静态流式布局 */
  .amc-sidebar{ position: static; height: 100%; }
  .amc-main{ left: 0; width: auto; height: auto; }
}

@media (max-width: 1024px) {
  .amc-sidebar{
    width: 280px;
  }
  
  .amc-main{
    left: 280px;
    width: calc(100vw - 280px);
  }
  
  .course-basic-info{
    flex-direction: column;
    text-align: center;
  }
}

/* === 对齐 AdminCourses 的个人信息卡样式 === */

/* 头像：与第一页一致，补上边框 */
.amc-profile-card .avatar{
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  background: #F4F6FA;
  display: grid;
  place-items: center;
  border: 1px solid #EAEAEA !important; /* 等同 var(--ac-border) */
}

/* 对齐 AdminCourses：姓名与邮箱用默认行高(normal) */
.amc-profile-card .info .name{
  /* 用 font 简写一次性锁定：字重600、16px、line-height:normal、字体族一致 */
  font: 600 16px/normal Montserrat, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  color: #172239;
  margin: 0;            /* 确保无额外间距 */
}

.amc-profile-card .info .email{
  /* 400、12px、line-height:normal，与 Courses 页一致 */
  font: 400 12px/normal Montserrat, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  color: #6D6D78;
  margin: 0;
}

/* 右侧箭头按钮与第一页一致的外观 */
.amc-profile-card .chevron{
  background: #fff;
  border: 1px solid #EAEAEA;
  border-radius: 999px;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  cursor: pointer;
}

@media (max-width: 768px) {
  .admin-manage-course-layout{
    flex-direction: column;
  }
  
  .amc-sidebar{
    width: 100%;
    height: auto;
    position: static;
  }
  
  .amc-main{
    left: 0;
    width: 100%;
    height: auto;
  }
  
  .course-detail-card{
    width: 100%;
    margin-top: 24px;
  }
}

/* 让 Manage 页的登出按钮与 Courses 页完全一致 */
.amc-sidebar .btn-outline{
  padding:14px;
  border-radius:14px;
  background:#fff;
  border:1px solid var(--amc-border);
  cursor:pointer;
  margin-top:auto;

  /* 关键：显式指定为 Courses 页的计算值，并压过继承/UA 样式 */
  font-family: Arial, sans-serif !important;
  font-size: 13.3333px !important;
  font-weight: 600 !important;
  color: #000 !important;

  /* 取消之前的固定尺寸与居中网格，避免影响字体渲染 */
  width:auto !important;
  height:auto !important;
  display:block !important;
  text-align:center;
}

/* 创建任务弹窗样式 - 采用preference弹窗设计，紫色主题 */
.task-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: saturate(180%) blur(2px);
  z-index: 1000;
  will-change: transform;
}

.task-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 520px;
  max-width: 92vw;
  background: #fff;
  border-radius: 20px;
  border: 2px solid #BB87AC; /* 紫色边框，类似preference弹窗 */
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.12);
  padding: 28px;
  z-index: 1010;
  will-change: transform;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.task-modal-header {
  position: relative;
  padding: 0 0 16px 0;
  border-bottom: none;
  flex-shrink: 0;
}

.task-modal-title {
  text-align: center;
  font-weight: 800;
  font-size: 22px;
  margin: 4px 0 16px;
  color: #172239;
  font-family: 'Montserrat', sans-serif;
}

.task-modal-close {
  position: absolute;
  left: 12px;
  top: 12px;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 1px solid var(--sh-border, #D0D5DD);
  background: #fff;
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #6D6D78;
  transition: all 0.2s ease;
}

.task-modal-close:hover {
  background: #BB87AC; /* 紫色背景 */
  border-color: #BB87AC;
  color: white;
}

.task-modal-content {
  flex: 1;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
}

.task-input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-label {
  font-size: 16px;
  font-weight: 600;
  color: #172239;
  font-family: 'Montserrat', sans-serif;
}

.task-label .required {
  color: #E31B54;
  margin-left: 4px;
}

.task-input {
  width: 100%;
  max-width: 400px;
  height: 40px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #D0D5DD;
  padding: 0 16px;
  font-size: 14px;
  font-family: 'Montserrat', sans-serif;
  box-sizing: border-box;
  transition: border-color 0.2s ease;
}

.task-input:focus {
  outline: none;
  border-color: #BB87AC; /* 紫色焦点边框 */
}

.task-error {
  font-size: 12px;
  color: #DD5151;
  font-weight: 400;
  letter-spacing: 0.5px;
}

.file-upload-area {
  width: 100%;
  max-width: 400px;
  height: 80px;
  background: rgba(248, 249, 250, 0.8);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  position: relative;
  border: 1px dashed #D0D5DD;
  box-sizing: border-box;
  transition: border-color 0.2s ease;
}

.file-upload-area:hover {
  border-color: #BB87AC; /* 紫色悬停边框 */
}

.file-upload-icon {
  font-size: 24px;
}

.file-upload-text {
  font-size: 16px;
  color: #6D6D78;
  font-weight: 400;
  font-family: 'Montserrat', sans-serif;
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.task-modal-footer {
  padding: 24px 32px;
  display: flex;
  justify-content: center;
  gap: 16px;
  border-top: 1px solid #EAEAEA;
  flex-shrink: 0;
}

.task-create-btn {
  width: 120px;
  height: 40px;
  background: #BB87AC; /* 紫色背景 */
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Montserrat', sans-serif;
  transition: background 0.2s ease;
}

.task-create-btn:not(:disabled):hover {
  background: #A57598; /* 深紫色悬停 */
}

.task-create-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 上传材料弹窗样式 - 采用preference弹窗设计，紫色主题 */
.material-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: saturate(180%) blur(2px);
  z-index: 1000;
  will-change: transform;
}

.material-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 520px;
  max-width: 92vw;
  background: #fff;
  border-radius: 20px;
  border: 2px solid #BB87AC; /* 紫色边框，类似preference弹窗 */
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.12);
  padding: 28px;
  z-index: 1010;
  will-change: transform;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.material-modal-header {
  position: relative;
  padding: 0 0 16px 0;
  border-bottom: none;
  flex-shrink: 0;
}

.material-modal-title {
  text-align: center;
  font-weight: 800;
  font-size: 22px;
  margin: 4px 0 16px;
  color: #172239;
  font-family: 'Montserrat', sans-serif;
}

.material-modal-close {
  position: absolute;
  left: 12px;
  top: 12px;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 1px solid var(--sh-border, #D0D5DD);
  background: #fff;
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #6D6D78;
  transition: all 0.2s ease;
}

.material-modal-close:hover {
  background: #BB87AC; /* 紫色背景 */
  border-color: #BB87AC;
  color: white;
}

.material-modal-content {
  flex: 1;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
}

.material-input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.material-label {
  font-size: 16px;
  font-weight: 600;
  color: #172239;
  font-family: 'Montserrat', sans-serif;
}

.material-label .required {
  color: #E31B54;
  margin-left: 4px;
}

.material-input {
  padding: 12px 16px;
  border: 1px solid #D0D5DD;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  font-family: 'Montserrat', sans-serif;
  transition: border-color 0.2s ease;
}

.material-input:focus {
  outline: none;
  border-color: #BB87AC; /* 紫色焦点边框 */
}

.material-textarea {
  padding: 12px 16px;
  border: 1px solid #D0D5DD;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  font-family: 'Montserrat', sans-serif;
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.2s ease;
}

.material-textarea:focus {
  outline: none;
  border-color: #BB87AC; /* 紫色焦点边框 */
}

.material-error {
  font-size: 12px;
  color: #DD5151;
  font-weight: 400;
  letter-spacing: 0.5px;
}

.material-file-upload-area {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px dashed #D0D5DD;
  border-radius: 8px;
  background: rgba(248, 249, 250, 0.8);
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.material-file-upload-area:hover {
  border-color: #BB87AC; /* 紫色悬停边框 */
}

.material-file-upload-icon {
  font-size: 20px;
}

.material-file-upload-text {
  font-size: 16px;
  color: #6D6D78;
  font-weight: 400;
  font-family: 'Montserrat', sans-serif;
}

.material-file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.material-modal-footer {
  padding: 24px 32px;
  display: flex;
  justify-content: center;
  gap: 16px;
  border-top: 1px solid #EAEAEA;
  flex-shrink: 0;
}

.material-create-btn {
  width: 120px;
  height: 40px;
  background: #BB87AC; /* 紫色背景 */
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Montserrat', sans-serif;
  transition: background 0.2s ease;
}

.material-create-btn:not(:disabled):hover {
  background: #A57598; /* 深紫色悬停 */
}

.material-create-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 创建题目弹窗样式 - 采用preference弹窗设计，紫色主题 */
.question-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: saturate(180%) blur(2px);
  z-index: 1000;
  will-change: transform;
}

.question-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  max-width: 92vw;
  background: #fff;
  border-radius: 20px;
  border: 2px solid #BB87AC; /* 紫色边框，类似preference弹窗 */
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.12);
  padding: 28px;
  z-index: 1010;
  will-change: transform;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.question-modal-header {
  position: relative;
  padding: 0 0 16px 0;
  border-bottom: none;
  flex-shrink: 0;
}

.question-modal-title {
  text-align: center;
  font-weight: 800;
  font-size: 22px;
  margin: 4px 0 16px;
  color: #172239;
  font-family: 'Montserrat', sans-serif;
}

.question-modal-close {
  position: absolute;
  left: 12px;
  top: 12px;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 1px solid var(--sh-border, #D0D5DD);
  background: #fff;
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #6D6D78;
  transition: all 0.2s ease;
}

.question-modal-close:hover {
  background: #BB87AC; /* 紫色背景 */
  border-color: #BB87AC;
  color: white;
}

.question-modal-content {
  flex: 1;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
}

/* 文件上传区样式 */
.question-file-upload-section {
  background: linear-gradient(135deg, #f8f4ff 0%, #fff5f8 100%);
  border: 2px dashed #BB87AC;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 8px;
}

.upload-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.upload-icon {
  font-size: 24px;
}

.upload-title {
  font-size: 16px;
  font-weight: 700;
  color: #172239;
  font-family: 'Montserrat', sans-serif;
}

.upload-description {
  font-size: 13px;
  color: #6D6D78;
  margin-bottom: 16px;
  line-height: 1.4;
}

.upload-input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.upload-button {
  padding: 10px 24px;
  background: #BB87AC;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Montserrat', sans-serif;
}

.upload-button:hover {
  background: #a676a0;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(187, 135, 172, 0.3);
}

.upload-error {
  color: #E31B54;
  font-size: 13px;
  font-weight: 500;
}

.upload-format-guide {
  margin-top: 16px;
  border-top: 1px solid #e0d5e8;
  padding-top: 12px;
}

.upload-format-guide summary {
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: #BB87AC;
  padding: 4px 0;
  user-select: none;
}

.upload-format-guide summary:hover {
  color: #a676a0;
}

.format-content {
  margin-top: 12px;
  font-size: 12px;
  color: #172239;
}

.format-content p {
  margin: 8px 0 4px;
  font-weight: 600;
}

.format-note {
  background: #fffbf0;
  border-left: 3px solid #BB87AC;
  padding: 8px 12px;
  margin: 4px 0 12px;
  font-size: 11px;
  color: #6D6D78;
  border-radius: 4px;
}

.format-example {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 12px;
  font-size: 11px;
  line-height: 1.5;
  overflow-x: auto;
  color: #2d3748;
  font-family: 'Monaco', 'Courier New', monospace;
  margin: 4px 0 12px;
}

.question-input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-label {
  font-size: 16px;
  font-weight: 600;
  color: #172239;
  font-family: 'Montserrat', sans-serif;
}

.question-label .required {
  color: #E31B54;
  margin-left: 4px;
}

.question-input {
  width: 100%;
  height: 40px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #D0D5DD;
  padding: 0 16px;
  font-size: 14px;
  font-family: 'Montserrat', sans-serif;
  box-sizing: border-box;
  transition: border-color 0.2s ease;
}

.question-input:focus {
  outline: none;
  border-color: #BB87AC; /* 紫色焦点边框 */
}

.question-textarea {
  padding: 12px 16px;
  border: 1px solid #D0D5DD;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  font-family: 'Montserrat', sans-serif;
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.2s ease;
}

.question-textarea:focus {
  outline: none;
  border-color: #BB87AC; /* 紫色焦点边框 */
}

.question-error {
  font-size: 12px;
  color: #DD5151;
  font-weight: 400;
  letter-spacing: 0.5px;
}

.question-type-selector {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.type-option {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #D0D5DD;
  border-radius: 8px;
  background: #fff;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
}

.type-option.selected {
  border-color: #BB87AC;
  background: #BB87AC;
  color: white;
}

.option-input-group {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.option-label {
  font-weight: 600;
  color: #172239;
  min-width: 60px;
}

.option-input {
  flex: 1;
  height: 36px;
  border: 1px solid #D0D5DD;
  border-radius: 6px;
  padding: 0 12px;
  font-size: 14px;
  transition: border-color 0.2s ease;
}

.option-input:focus {
  outline: none;
  border-color: #BB87AC;
}

.question-modal-footer {
  padding: 24px 32px;
  display: flex;
  justify-content: center;
  gap: 16px;
  border-top: 1px solid #EAEAEA;
  flex-shrink: 0;
}

.question-create-btn {
  width: 120px;
  height: 40px;
  background: #BB87AC; /* 紫色背景 */
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Montserrat', sans-serif;
  transition: background 0.2s ease;
}

.question-create-btn:not(:disabled):hover {
  background: #A57598; /* 深紫色悬停 */
}

.question-create-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 批量创建按钮样式 */
.batch-create-btn {
  width: auto !important;
  min-width: 200px;
  padding: 0 24px;
}

.question-cancel-btn {
  width: 120px;
  height: 40px;
  background: #F5F5F5;
  border: 1px solid #CCCCCC;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333333;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Montserrat', sans-serif;
  transition: all 0.2s ease;
}

.question-cancel-btn:hover {
  background: #E8E8E8;
  border-color: #999999;
}

/* 批量导航样式 */
.batch-navigation {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.batch-nav-btn {
  padding: 6px 12px;
  background: #F5F5F5;
  border: 1px solid #CCCCCC;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #333333;
  cursor: pointer;
  transition: all 0.2s ease;
}

.batch-nav-btn:hover:not(:disabled) {
  background: #E8E8E8;
  border-color: #999999;
}

.batch-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.batch-indicator {
  font-size: 14px;
  font-weight: 600;
  color: #BB87AC;
  min-width: 60px;
  text-align: center;
}

/* 批量上传提示 */
.batch-note {
  background: linear-gradient(135deg, #FFF4E6 0%, #FFE6F0 100%);
  border-left: 4px solid #BB87AC;
  padding: 12px 16px;
  margin-bottom: 16px;
}

/* 示例文件下载链接 */
.sample-link {
  display: inline-block;
  padding: 6px 12px;
  background: #F0E6FF;
  border: 1px solid #BB87AC;
  border-radius: 6px;
  color: #BB87AC;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.sample-link:hover {
  background: #BB87AC;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(187, 135, 172, 0.3);
}
`;