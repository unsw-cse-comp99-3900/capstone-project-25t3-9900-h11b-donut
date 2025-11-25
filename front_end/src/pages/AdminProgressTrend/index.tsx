import { useState, useEffect, useMemo } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import {
  ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine
} from 'recharts'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconMonitor from '../../assets/icons/bell-24.svg'
import adminHomepageImage from '../../assets/images/admin-homepage.png'
import apiService from '../../services/api'

type StudentProgress = {
  id: string;
  name: string;
  studentId: string;
  completionPercent: number;
  overdueCount: number;

  bonus: string; 
};

type CreatedCourse = {
  id: string;
  title: string;
  description: string;
  illustrationIndex: number;
  tasks: Array<{
    id: string;
    title: string;
    deadline: string;
  }>;
};


type RosterStudent = {
  name: string;
  studentId: string;
};

type Part = {
  studentId: string;
  scheduled_date: string;   // ISO 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:mm:ss'
  done_date?: string | null;
  weight?: number;         //optional
};

type TrendPoint = {
  dateISO: string;   // 'YYYY-MM-DD'
  label: string;     // 'MM/DD' 
  scheduled: number; // denominator
  onTime: number;    // numerator
  ratePct: number | null; // Percentage, null when denominator=0
};

export function AdminProgressTrend() {
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<string>('')
  const [selectedTask, setSelectedTask] = useState<string>('')
  const [students, setStudents] = useState<StudentProgress[]>([])
  const [filteredStudents, setFilteredStudents] = useState<StudentProgress[]>([])
  const [progressFilter, setProgressFilter] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState<string>('')
  
  const uid = localStorage.getItem('current_user_id') || '';
  
  const safeJSON = <T,>(key: string, fallback: T): T => {
    try {
      const s = localStorage.getItem(key);
      return s ? (JSON.parse(s) as T) : fallback;
    } catch {
      return fallback;
    }
  };

  const [createdCourses, setCreatedCourses] = useState<CreatedCourse[]>(() => {
    if (!uid) return [];
    const rawCourses = safeJSON<any[]>(`admin:${uid}:courses`, []);
    const tasksMap = safeJSON<Record<string, any[]>>(`admin:${uid}:tasks`, {});
    return rawCourses.map((c) => {
      const courseId = String(c.id ?? c.code); 
      const courseTasks = tasksMap[courseId] ?? [];
      return {
        id: courseId,
        title: c.title ?? '',
        description: c.desc ?? c.description ?? '',
        illustrationIndex: Number.isFinite(c.illustrationIndex) ? c.illustrationIndex : 0,
        tasks: courseTasks.map((t) => ({
          id: t.id != null ? String(t.id) : `task_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
          title: t.title ?? 'Untitled Task',
          deadline: t.deadline ?? 'No deadline',
        })),
      };
    });
  });

  const [user] = useState<{ name?: string; email?: string; avatarUrl?: string } | null>(() => {
    if (!uid) return null;
    try { return JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null'); }
    catch { return null; }
  });

  useEffect(() => {
    const getParams = () => {
      if (window.location.hash.includes('?')) {
        return new URLSearchParams(window.location.hash.split('?')[1]);
      }
      return new URLSearchParams(window.location.search.replace(/^\?/, ''));
    };
    
    const params = getParams();
    const courseId = params.get('courseId');
    const taskId = params.get('taskId');
    
    if (courseId && taskId) {
      setSelectedCourse(courseId);
      setSelectedTask(taskId);
      loadStudentProgress(courseId, taskId);
    }
  }, []);

  useEffect(() => {
    //Monitor changes in localStorage to update course data
    const handleStorageChange = () => {
      try {
        const saved = localStorage.getItem('admin_created_courses');
        if (saved) {
          setCreatedCourses(JSON.parse(saved));
        }
      } catch {
        setCreatedCourses([]);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [uid]);

  const loadStudentProgress = (courseId: string, taskId: string) => {

    console.log('Loading student progress for course:', courseId, 'task:', taskId);

  };

  useEffect(() => {

    let result = [...students];

    if (progressFilter !== 'all') {
      result = result.filter(student => {
        switch (progressFilter) {
          case '0-10': return student.completionPercent <= 10;
          case '10-40': return student.completionPercent > 10 && student.completionPercent <= 40;
          case '40-70': return student.completionPercent > 40 && student.completionPercent <= 70;
          case '70-100': return student.completionPercent > 70;
          default: return true;
        }
      });
    }
    

    if (searchTerm) {
      result = result.filter(student => 
        student.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Sort by Name A → Z
    result = result.sort((a, b) => a.name.localeCompare(b.name));
    
    setFilteredStudents(result);
  }, [students, progressFilter, searchTerm]);

  const handleLogout = () => {
    setLogoutModalOpen(true)
  }

  const confirmLogout = async () => {
    try { await apiService.logout(); }
    finally {
      window.location.hash = '#/login-admin';
      setLogoutModalOpen(false);
    }
  };

  const getSelectedCourse = () => {
    return createdCourses.find(course => course.id === selectedCourse);
  };

  const getSelectedTask = () => {
    const course = getSelectedCourse();
    return course?.tasks.find(task => task.id === selectedTask);
  };

//Build 7-day on-time performance trend data (based on parts aggregation of selected Course+Task)
  function buildTrendSeries(parts: Part[], today = new Date()): TrendPoint[] {
    // recent 7 days
    const dayKeys: string[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date(today);
      d.setHours(0,0,0,0);
      d.setDate(d.getDate() - i);
      dayKeys.push(d.toISOString().slice(0, 10));
    }
    
  
    const bucket: Record<string, { scheduled: number; onTime: number }> = {};
    for (const k of dayKeys) bucket[k] = { scheduled: 0, onTime: 0 };

    for (const p of parts) {
      const scheduledDate = (p.scheduled_date || '').slice(0,10);
      if (!bucket[scheduledDate]) continue; 
      
      bucket[scheduledDate].scheduled++;

      const doneSameDay = p.done_date && p.done_date.slice(0,10) === scheduledDate;
      if (doneSameDay) {
        bucket[scheduledDate].onTime++;
      }
    }

    const fmt = (dISO: string) => {
      const d = new Date(dISO);
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      return `${mm}/${dd}`;
    };

    return dayKeys.map(k => {
      const { scheduled, onTime } = bucket[k] || { scheduled: 0, onTime: 0 };
      
      const ratePct = scheduled > 0 ? Math.round(onTime * 100 / scheduled) : null;
      
      return { 
        dateISO: k, 
        label: fmt(k), 
        scheduled, 
        onTime, 
        ratePct 
      };
    });
  }
// mock part, just skip, has been updated now but not removing
  const generateMockRoster = (): RosterStudent[] => {
    return [
      { name: 'Alice Johnson', studentId: 'z1234567' },
      { name: 'Bob Smith', studentId: 'z2345678' },
      { name: 'Carol Davis', studentId: 'z3456789' },
      { name: 'David Wilson', studentId: 'z4567890' },
      { name: 'Eva Brown', studentId: 'z5678901' },
      { name: 'Frank Miller', studentId: 'z6789012' },
      { name: 'Grace Lee', studentId: 'z7890123' },
      { name: 'Henry Chen', studentId: 'z8901234' },
      { name: 'Ivy Zhang', studentId: 'z9012345' },
    ];
  };

  const generateMockParts = (_courseId?: string, _taskId?: string): Part[] => {
    const parts: Part[] = [];
    const today = new Date();
    const roster = generateMockRoster();
    

    roster.forEach((student, _index) => {
      const studentId = student.studentId;

      const studentHash = studentId.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
      const partCount = (studentHash % 5) + 2; 
      
      for (let i = 0; i < partCount; i++) {

        const daysAgo = (studentHash + i) % 7;
        const scheduledDate = new Date(today);
        scheduledDate.setDate(today.getDate() - daysAgo);
        const scheduledDateStr = scheduledDate.toISOString().split('T')[0];

        const completionHash = (studentHash + i * 13) % 100;
        const isDone = completionHash < 70;
        let doneDateStr: string | null = null;
        
        if (isDone) {
          const doneDelay = (studentHash + i * 7) % 3;
          const doneDate = new Date(scheduledDate);
          doneDate.setDate(scheduledDate.getDate() + doneDelay);
          doneDateStr = doneDate.toISOString().split('T')[0];
        }

        const weight = (studentHash % 3) + 1;
        
        parts.push({
          studentId: studentId,
          scheduled_date: scheduledDateStr,
          done_date: doneDateStr,
          weight: weight
        });
      }
    });
    
    return parts;
  };

  const calculateStudentProgress = (studentId: string, parts: Part[]): { completionPercent: number, overdueCount: number } => {
    const studentParts = parts.filter(part => part.studentId === studentId);
    const today = new Date().toISOString().split('T')[0];
    
    //If there are no parts or all future plans → Completion%=0, Overdue=0
    if (studentParts.length === 0) {
      return { completionPercent: 0, overdueCount: 0 };
    }
    
    // Check if all are future plans
    const allFutureParts = studentParts.every(part => part.scheduled_date > today);
    if (allFutureParts) {
      return { completionPercent: 0, overdueCount: 0 };
    }
    
    // Calculate Completion% (binary+weight/equal weight)
    let totalWeight = 0;
    let completedWeight = 0;
    
    studentParts.forEach(part => {
      // Only calculate past and current parts
      if (part.scheduled_date <= today) {
        const weight = part.weight || 1; 
        totalWeight += weight;
        
        // done_date->Done
        if (part.done_date) {
          completedWeight += weight;
        }
      }
    });
    
    let completionPercent = 0;
    if (totalWeight > 0) {
      completionPercent = Math.round((completedWeight / totalWeight) * 100);

      completionPercent = Math.max(0, Math.min(100, completionPercent));
    }
    
    // calculate Overdue
    let overdueCount = 0;
    studentParts.forEach(part => {
   
      if (part.scheduled_date <= today) {
        const isOverdue = 
          // rule1：done_date > scheduled_date
          (part.done_date && part.done_date > part.scheduled_date) ||
          // rule2：done_date is null and scheduled_date < today
          (!part.done_date && part.scheduled_date < today);
        
        if (isOverdue) {
          overdueCount += 1;
        }
      }
    });
    
    return { completionPercent, overdueCount };
  };
  
  // Generate progress data for all students
  const generateStudentProgressData = (roster: RosterStudent[], parts: Part[]): StudentProgress[] => {
    return roster.map((student, index) => {
      const { completionPercent, overdueCount } = calculateStudentProgress(student.studentId, parts);
      return {
        id: (index + 1).toString(),
        name: student.name,
        studentId: student.studentId,
        completionPercent,
        overdueCount,

        bonus: (Math.random() * 2).toFixed(2), 
      };
    });
  };
  

  
  const useMock = false; 
  const [roster, setRoster] = useState<RosterStudent[]>([]);
  const [parts, setParts] = useState<Part[]>([]);
  

  useEffect(() => {
    const loadData = () => {
      if (useMock) {
        const mockRoster = generateMockRoster();
        const mockParts = generateMockParts(selectedCourse, selectedTask);
        

        localStorage.setItem('mock_roster_data', JSON.stringify(mockRoster));
        localStorage.setItem('mock_parts_data', JSON.stringify(mockParts));
        
        setRoster(mockRoster);
        setParts(mockParts);
        console.log('Using frontend mock data, based on the selected Course+Task, it has been stored in local storage');
      } else {
        (async () => {
          try {
            if (!selectedCourse) return;
            const list = await apiService.adminGetCourseStudentsProgress(selectedCourse, selectedTask);
            const mockPartsNow = generateMockParts(selectedCourse, selectedTask);
            setParts(mockPartsNow);
            const mapped = list.map((it, idx) => ({
              id: String(idx + 1),
              name: it.name,                   
              studentId: it.student_id,        
              completionPercent: it.progress,   
              overdueCount: it.overdue_count ?? 0, 

              bonus: it.bonus != null ? Number(it.bonus).toFixed(2) : "0.00", 
            } as StudentProgress));
            const sorted = [...mapped].sort((a, b) => a.name.localeCompare(b.name));
            setStudents(sorted);
            setFilteredStudents(sorted);
          } catch (e) {
            console.error('[AdminProgressTrend] load backend progress failed:', e);
            setStudents([]);
            setFilteredStudents([]);
          }
        })();
      }
    };
    
    loadData();
  }, [useMock, selectedCourse, selectedTask]);
  
  const mockRoster = roster;
  const mockParts = parts;
  

  const studentProgressData = useMemo(() => 
    generateStudentProgressData(mockRoster, mockParts), 
    [mockRoster, mockParts]
  );
  
  const trendSeries = useMemo(() => buildTrendSeries(mockParts), [mockParts]);


  
  useEffect(() => {

    if (!useMock) return;
    const sorted = [...studentProgressData].sort((a, b) => a.name.localeCompare(b.name));
    setStudents(sorted);
    setFilteredStudents(sorted);
  }, [studentProgressData, useMock]);
  

  const TrendChart = ({ series }: { series: TrendPoint[] }) => {
   
    const hasAnyScheduled = series.some(d => d.scheduled > 0);
    if (!hasAnyScheduled) return <div className="chart-empty">No parts scheduled in the last 7 days.</div>;

    return (
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={series} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          {/* left：quantity */}
          <YAxis yAxisId="left" allowDecimals={false} width={36} />
          {/* right：percentage 0–100 */}
          <YAxis yAxisId="right" orientation="right" domain={[0, 100]}
                 tickFormatter={(v) => `${v}%`} width={44} />
          <Tooltip
            formatter={(value: any, name: any, _ctx: any) => {
              if (name === 'ratePct') return [`${value === null ? '—' : `${value}%`}`, 'On-time rate'];
              if (name === 'scheduled') return [value, 'Scheduled parts'];
              return [value, name];
            }}
            labelFormatter={(_, payload: readonly any[]) => {
              const p = payload?.[0]?.payload as TrendPoint;
              return `${p.label}  •  ${p.scheduled ? `${p.onTime}/${p.scheduled}` : '—'}`;
            }}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px'
            }}
            itemStyle={{
              color: '#333', 
              fontWeight: 'normal'
            }}
            labelStyle={{
              color: '#333', 
              fontWeight: '600'
            }}
          />

          <Bar yAxisId="left" dataKey="scheduled" barSize={14}
               radius={[6,6,6,6]} fill="#E9E9EE" />

          <Line yAxisId="right" dataKey="ratePct" type="linear"
                connectNulls={false} dot={{ r: 3 }}
                stroke="var(--ah-primary)" strokeWidth={2} />

          <ReferenceLine yAxisId="right" y={80} stroke="#9aa0a6" strokeDasharray="4 4" />
        </ComposedChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div key={uid} className="admin-progress-trend-layout">
      {/* Left navigation bar - completely consistent with AdminMonitor*/}
      <aside className="ah-sidebar">
        <div className="ah-profile-card">
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

        <nav className="ah-nav">
          <a className="item" href="#/admin-home">
            <img src={IconHome} className="nav-icon" alt="" /> Home
          </a>
          <a className="item" href="#/admin-courses">
            <img src={IconCourses} className="nav-icon" alt="" /> My Courses
          </a>
          <a className="item active" href="#/admin-monitor">
            <img src={IconMonitor} className="nav-icon" alt="" /> Analytics
          </a>
        </nav>

        <div className="ah-illustration">
          <img src={adminHomepageImage} alt="Admin Dashboard" style={{ width: '100%', height: 'auto', borderRadius: '20px' }} />
        </div>

        <button className="btn-outline" onClick={handleLogout}>Log Out</button>
      </aside>

      {/* Right main content area - outermost wrapping box */}
      <div className="apt-outer-container">
        <main className="apt-main">
          <header className="apt-header">
            <div className="header-content">
              <div className="cd-hero-clean">
                <button
                  className="back-circle"
                  aria-label="Back to Analytics"
                  onClick={() => window.location.hash = '#/admin-monitor'}
                >
                  <img src={ArrowRight} width={16} height={16} alt="" className="chev-left" />
                </button>
              </div>
              <div className="left">
                <div className="hello">Progress & Trend</div>
                <h1 className="title">
                  {getSelectedCourse()?.title || 'Course'} - {getSelectedTask()?.title || 'Task'}
                </h1>
              </div>
            </div>
          </header>

          {/* Scrollable content area */}
          <div className="apt-scrollable-content">
          {/* Filter area */}
          <section className="apt-filters">
            <div className="progress-filters">
              <span className="filter-label">Progress Filter:</span>
              <button 
                className={`filter-btn ${progressFilter === 'all' ? 'active' : ''}`}
                onClick={() => setProgressFilter('all')}
              >
                All Students
              </button>
              <button 
                className={`filter-btn ${progressFilter === '0-10' ? 'active' : ''}`}
                onClick={() => setProgressFilter('0-10')}
              >
                ≤10%
              </button>
              <button 
                className={`filter-btn ${progressFilter === '10-40' ? 'active' : ''}`}
                onClick={() => setProgressFilter('10-40')}
              >
                10-40%
              </button>
              <button 
                className={`filter-btn ${progressFilter === '40-70' ? 'active' : ''}`}
                onClick={() => setProgressFilter('40-70')}
              >
                40-70%
              </button>
              <button 
                className={`filter-btn ${progressFilter === '70-100' ? 'active' : ''}`}
                onClick={() => setProgressFilter('70-100')}
              >
                70-100%
              </button>
            </div>
            
            <div className="search-filter">
              <input
                type="text"
                placeholder="Search students..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>
          </section>

          {/* Student Progress Table */}
          <section className="apt-table-section">
            {filteredStudents.length === 0 ? (
              <div className="empty-state">
                <div className="empty-title">
                  {students.length === 0 ? 'No students found' : 'No students match your filters'}
                </div>
                <div className="empty-subtitle">
                  {students.length === 0 ? 'There are no students enrolled in this course.' : 'Try adjusting your filters or search term.'}
                </div>
              </div>
            ) : (
              <div className="students-table">
                <div className="table-header">
                  <div className="header-cell student-col">Student Name</div>
                  <div className="header-cell student-id-col">Student ID</div>
                  <div className="header-cell completion-col">Completion%</div>
                  <div className="header-cell overdue-col">Overdue</div>
                  <div className="header-cell bonus-col">Bonus</div>
                </div>
                
                <div className="table-body">
                  {filteredStudents.map((student) => (
                    <div key={student.id} className="table-row">
                      <div className="cell student-col">{student.name}</div>
                      <div className="cell student-id-col">{student.studentId}</div>
                      <div className="cell completion-col">
                        <div className="progress-bar-container">
                          <div 
                            className="progress-bar"
                            style={{ width: `${student.completionPercent}%` }}
                          ></div>
                          <span className="progress-text">{student.completionPercent}%</span>
                        </div>
                      </div>
                      <div className="cell overdue-col">{student.overdueCount}</div>
                      <div className="cell bonus-col">{student.bonus}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>


        </div>
      </main>
      </div>

      <ConfirmationModal
        isOpen={logoutModalOpen}
        onClose={() => setLogoutModalOpen(false)}
        onConfirm={confirmLogout}
        title="Log Out"
        message="Are you sure you want to log out?"
        confirmText="Confirm"
        cancelText="Cancel"
      />

      <style>{css}</style>
    </div>
  )
}

/* Progress & Trend页面样式 */
const css = `
:root{
  --ah-border: #EAEAEA;
  --ah-muted: #6D6D78;
  --ah-text: #172239;
  --ah-card-bg:#FFFFFF;
  --ah-shadow: 0 8px 24px rgba(0,0,0,0.04);
  --ah-primary: #BB87AC; /* 管理员紫色主题 */
  --ah-primary-light: rgba(187, 135, 172, 0.49); /* 半透明紫色 */
  
  /* 补齐变量映射 */
  --am-border: var(--ah-border);
  --am-muted: var(--ah-muted);
  --am-text: var(--ah-text);
  --am-card-bg: var(--ah-card-bg);
  --am-primary: var(--ah-primary);
}

.admin-progress-trend-layout{
  display:grid;
  grid-template-columns: 280px 1fr;
  gap:48px;
  padding:32px;
  color:var(--ah-text);
  background:#fff;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  min-height: 100vh;
}

/* 左侧导航栏样式 - 与AdminHome完全一致 */
.ah-sidebar{
  display:flex;
  flex-direction:column;
  gap:24px;
  height: 100%;
}

.ah-profile-card{
  display:flex;align-items:center;gap:12px;
  padding:16px;border:1px solid var(--ah-border);border-radius:20px;background:var(--ah-card-bg);box-shadow:var(--ah-shadow);
  height: 95.36px;
}
.ah-profile-card .avatar{
  width:48px;height:48px;border-radius:50%;overflow:hidden;background:#F4F6FA;display:grid;place-items:center;border:1px solid var(--ah-border);
}
.ah-profile-card .info .name{font-size:16px;font-weight:600}
.ah-profile-card .info .email{color:var(--ah-muted);font-size:12px}
.ah-profile-card .chevron{margin-left:auto;background:#fff;border:1px solid var(--ah-border);border-radius:999px;width:36px;height:36px;display:grid;place-items:center;cursor:pointer;transition:background-color 0.2s}
.ah-profile-card .chevron:hover{background:var(--ah-primary-light)}

.ah-nav{
  display:flex;flex-direction:column;gap:12px;
  padding:16px;border:1px solid var(--ah-border);border-radius:20px;background:#fff;box-shadow:var(--ah-shadow);
}
.ah-nav .item{
  display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--ah-muted);text-decoration:none;font-weight:500;
  border: none;
  outline: none;
}
.ah-nav .item.active{background:var(--ah-primary);color:#172239;font-weight:600;border-radius:20px}
.ah-nav .nav-icon{width:20px;height:20px}

.ah-illustration{
  margin-top: auto;
  margin-bottom: 20px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-outline{
  padding:14px;
  border-radius:14px;
  background:#fff;
  border:1px solid var(--ah-border);
  cursor:pointer;
  font-weight:600;
  margin-top: auto;
}

/* 最外侧包裹框 */
.apt-outer-container{
  background: var(--ah-card-bg);
  border: 1px solid var(--ah-border);
  border-radius: 20px;
  box-shadow: var(--ah-shadow);
  overflow: hidden;
  height: calc(100vh - 64px);
}

/* 右侧主内容区域 */
.apt-main{
  display:flex;
  flex-direction:column;
  gap:32px;
  height: 100%;
  position: relative;
  padding: 24px;
  background: #f8f9fa; /* 浅浅的灰色背景 */
}

/* 固定标题区域 */
.apt-header{
  display:flex;
  align-items:flex-start;
  position: sticky;
  top: 0;
  background: #f8f9fa; /* 浅浅的灰色背景，与右侧主区域一致 */
  z-index: 10;
  padding: 0 0 16px 0;
  margin-bottom: -16px;
}

.header-content{
  display:flex;
  align-items:flex-start;
  gap:16px;
}

/* 可滚动内容区域 */
.apt-scrollable-content{
  display:flex;
  flex-direction:column;
  gap:32px;
  overflow-y: auto;
  padding-right: 8px;
  flex: 1;
}

.apt-header .left{
  display:flex;flex-direction:column;
  gap:8px;
}
.apt-header .hello{
  font-size:32px;font-weight:600;
  color:var(--ah-text);
}
.apt-header .title{
  font-size:18px;font-weight:400;
  color:var(--ah-muted);
  margin:0;
}

/* 返回按钮样式 - 与Admin Manage Course页面一致 */
.cd-hero-clean{
  position: relative;
  text-align: left;
  padding: 4px 0 8px;
  margin-bottom: 6px;
  background: transparent;
  display: flex;
  align-items: flex-start;
}

.back-circle{
  padding: 8px;
  border: 1px solid var(--ah-border);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.back-circle:hover{
  background: var(--ah-primary-light);
  border-color: var(--ah-primary);
}

.chev-left{
  transform: rotate(180deg);
}

.back-btn{
  padding:12px 24px;
  border:1px solid var(--ah-border);
  border-radius:8px;
  background:#fff;
  color:var(--ah-text);
  cursor:pointer;
  font-weight:500;
  transition:all 0.2s ease;
}

.back-btn:hover{
  background:var(--ah-primary-light);
  border-color:var(--ah-primary);
}

/* 过滤器区域 */
.apt-filters{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:24px;
  padding:20px;
  background:var(--ah-card-bg);
  border-radius:12px;
  border:1px solid var(--ah-border);
}

.progress-filters{
  display:flex;
  align-items:center;
  gap:12px;
  flex-wrap:wrap;
}

.filter-label{
  font-weight:600;
  color:var(--ah-text);
  white-space:nowrap;
}

.filter-btn{
  padding:8px 16px;
  border:1px solid var(--ah-border);
  border-radius:6px;
  background:#fff;
  color:var(--ah-muted);
  cursor:pointer;
  font-size:14px;
  transition:all 0.2s ease;
}

.filter-btn:hover{
  border-color:var(--ah-primary);
}

.filter-btn.active{
  background:var(--ah-primary);
  color:white;
  border-color:var(--ah-primary);
}

.search-input{
  padding:8px 12px;
  border:1px solid var(--ah-border);
  border-radius:6px;
  font-size:14px;
  min-width:200px;
}

/* 学生进度表格 */
.apt-table-section{
  flex:1;
}

.empty-state{
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  height:200px;text-align:center;
  background:var(--ah-card-bg);
  border-radius:12px;
  border:1px solid var(--ah-border);
}
.empty-state .empty-title{
  font-size:18px;font-weight:600;
  color:var(--ah-text);
  margin-bottom:8px;
}
.empty-state .empty-subtitle{
  font-size:14px;color:var(--ah-muted);
}

.students-table{
  background:var(--ah-card-bg);
  border-radius:12px;
  border:1px solid var(--ah-border);
  overflow:hidden;
}

.table-header{
  display:grid;
  grid-template-columns:1.5fr 1fr 1.5fr 0.8fr 0.8fr; /* 5列: 新增Bonus */
  gap:1px;
  background:var(--ah-border);
}

.header-cell{
  padding:16px 20px;
  background:var(--ah-primary);
  color:white;
  font-weight:600;
  font-size:14px;
  text-align:center;
}

.table-body{
  display:flex;
  flex-direction:column;
}

.table-row{
  display:grid;
  grid-template-columns:1.5fr 1fr 1.5fr 0.8fr 0.8fr; /* 新增第5列: Bonus */
  gap:1px;
  background:var(--ah-border);
  transition:background 0.2s ease;
}

.table-row:hover{
  background:var(--ah-primary-light);
}

.cell{
  padding:16px 20px;
  background:white;
  font-size:14px;
  display:flex;
  align-items:center;
}

/* 统一表格四列字体样式 */
.students-table .cell {
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: var(--ah-text); /* 黑色字体 */
}

/* 只保留对齐方式差异 */
.students-table .student-col {
  justify-content: center; /* 居中对齐 */
}

.students-table .student-id-col,
.students-table .completion-col {
  justify-content: center;
}

.progress-bar-container{
  position:relative;
  width:100%;
  height:24px;
  background:#f0f0f0;
  border-radius:12px;
  overflow:hidden;
}

.progress-bar{
  height:100%;
  background:var(--ah-primary);
  transition:width 0.3s ease;
}

.progress-text{
  position:absolute;
  top:50%;
  left:50%;
  transform:translate(-50%, -50%);
  font-size:12px;
  font-weight:500;
  color:var(--ah-text);
}

.students-table .overdue-col {
  justify-content: center;
}

.students-table .bonus-col {
  justify-content: center;
}

/* 趋势图表区域 */
.apt-trend-section{
  background:var(--ah-card-bg);
  border-radius:12px;
  border:1px solid var(--ah-border);
  padding:24px;
}

.trend-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:20px;
}

.trend-header h3{
  margin:0;
  font-size:18px;
  font-weight:600;
  color:var(--ah-text);
}

.trend-toggle{
  padding:8px 16px;
  border:1px solid var(--ah-border);
  border-radius:6px;
  background:#fff;
  color:var(--ah-muted);
  cursor:pointer;
  font-size:14px;
}

/* 趋势图表样式 */
.chart-container {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.chart-info {
  margin-bottom: 20px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ah-text);
  margin-bottom: 8px;
}

.chart-description {
  font-size: 12px;
  color: var(--ah-muted);
  line-height: 1.4;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--ah-muted);
  font-size: 14px;
  text-align: center;
}

/* 坐标轴标签说明样式 */
.chart-axis-labels {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid var(--ah-border);
}

.axis-label-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.axis-label {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.axis-title {
  font-weight: 600;
  color: var(--ah-text);
  font-size: 14px;
  min-width: 160px;
}

.axis-description {
  color: var(--ah-muted);
  font-size: 14px;
  line-height: 1.4;
}

/* 图表隐藏时的提示信息样式 */
.chart-hidden-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid var(--ah-border);
  text-align: center;
  padding: 20px;
}

.chart-hidden-message p {
  margin: 8px 0;
  color: var(--ah-muted);
  font-size: 14px;
  line-height: 1.4;
}

.chart-hidden-message p:first-child {
  font-weight: 600;
  color: var(--ah-text);
}

.chart-placeholder{
  height:200px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  background:#f8f9fa;
  border-radius:8px;
  border:2px dashed var(--ah-border);
  color:var(--ah-muted);
  text-align:center;
}

.chart-placeholder p{
  margin:4px 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .admin-progress-trend-layout{
    grid-template-columns: 240px 1fr;
  }
}

@media (max-width: 768px) {
  .admin-progress-trend-layout{
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
  }
  
  .ah-sidebar{
    order: 2;
  }
  
  .apt-main{
    max-height: none;
    overflow-y: visible;
  }
  
  .table-header,
  .table-row{
    grid-template-columns:1fr 1fr 1fr 1fr 0.8fr; /* 响应式: 5列 */
    gap:1px;
  }
  
  .header-cell,
  .cell{
    padding:12px 16px;
  }
  
  .progress-bar-container {
    min-width: 120px;
  }
}
`