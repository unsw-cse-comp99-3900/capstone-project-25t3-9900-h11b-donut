// AI计划生成服务 - 前端模拟实现

// 任务详情数据结构
export interface TaskDetail {
  id: string;
  courseId: string;
  title: string;
  description: string;
  deadline: string;
  parts: {
    id: string;
    title: string;
    estMinutes: number;
    weight?: number;
    dependsOn?: string[]; // 依赖的其他Part
  }[];
}

export interface TaskPart {
  id: string;
  title: string;
  description: string;
  estimatedMinutes: number;
  priority: number; // 1-5，1为最高优先级
  dependencies: string[]; // 依赖的其他part id
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface FeasibilityResult {
  isFeasible: boolean;
  totalTimeRequired: number;
  totalTimeAvailable: number;
  timeDeficit: number;
  suggestions: string[];
  warnings: string[];
}

export interface RelaxationStep {
  level: number;
  description: string;
  adjustments: {
    reduceTimePerPart?: number;
    extendDeadlineDays?: number;
    combineParts?: boolean;
    skipOptionalParts?: boolean;
  };
}

export class PlanGenerator {
  // AI拆分：根据任务类型和复杂度智能拆分
  static generateOrderedParts(task: TaskDetail): TaskPart[] {
    const parts: TaskPart[] = [];
    const taskType = this.analyzeTaskType(task.title, task.description);
    
    switch (taskType) {
      case 'research':
        parts.push(...this.createResearchParts());
        break;
      case 'coding':
        parts.push(...this.createCodingParts());
        break;
      case 'writing':
        parts.push(...this.createWritingParts());
        break;
      case 'presentation':
        parts.push(...this.createPresentationParts());
        break;
      default:
        parts.push(...this.createGenericParts());
    }

    // 根据deadline调整part数量和时长
    return this.adjustPartsByDeadline(parts, task.deadline);
  }

  // 可行性检查：评估时间是否足够
  static checkFeasibility(parts: TaskPart[], preferences: any): FeasibilityResult {
    const totalTimeRequired = parts.reduce((sum, part) => sum + part.estimatedMinutes, 0);
    const daysUntilDeadline = this.calculateDaysUntilDeadline(preferences.deadline);
    const dailyStudyHours = preferences.dailyHours || 2;
    const weeklyStudyDays = preferences.weeklyStudyDays || 5;
    
    // 计算可用时间（考虑avoid days）
    const availableDays = this.calculateAvailableDays(daysUntilDeadline, preferences.avoidDays, weeklyStudyDays);
    const totalTimeAvailable = availableDays * dailyStudyHours * 60; // 转换为分钟
    
    const timeDeficit = totalTimeRequired - totalTimeAvailable;
    const isFeasible = timeDeficit <= 0;

    const suggestions: string[] = [];
    const warnings: string[] = [];

    if (!isFeasible) {
      suggestions.push(`需要增加 ${Math.ceil(timeDeficit / 60)} 小时学习时间`);
      suggestions.push(`考虑将每日学习时间从 ${dailyStudyHours} 小时增加到 ${Math.ceil((totalTimeRequired / availableDays / 60) + 0.5)} 小时`);
      
      warnings.push(`时间不足！需要 ${Math.ceil(totalTimeRequired / 60)} 小时，但只有 ${Math.ceil(totalTimeAvailable / 60)} 小时可用`);
    }

    if (totalTimeRequired > dailyStudyHours * 60 * 7) { // 超过一周的满负荷
      warnings.push('任务量过大，建议与老师沟通调整截止日期');
    }

    return {
      isFeasible,
      totalTimeRequired,
      totalTimeAvailable,
      timeDeficit,
      suggestions,
      warnings
    };
  }

  // 放松阶梯：当时间不足时提供渐进式解决方案
  static applyRelaxation(parts: TaskPart[], preferences: any, currentLevel: number = 0): RelaxationStep[] {
    const steps: RelaxationStep[] = [];
    const feasibility = this.checkFeasibility(parts, preferences);
    
    if (feasibility.isFeasible) {
      return [{
        level: 0,
        description: '时间充足，无需调整',
        adjustments: {}
      }];
    }

    // 第一级：轻微时间压缩
    steps.push({
      level: 1,
      description: '轻微压缩每个part的时间（减少10%）',
      adjustments: {
        reduceTimePerPart: 0.1,
        combineParts: false,
        skipOptionalParts: false
      }
    });

    // 第二级：合并简单part
    steps.push({
      level: 2,
      description: '合并相邻的简单part，减少切换时间',
      adjustments: {
        reduceTimePerPart: 0.15,
        combineParts: true,
        skipOptionalParts: false
      }
    });

    // 第三级：跳过可选part
    steps.push({
      level: 3,
      description: '跳过非核心的optional part',
      adjustments: {
        reduceTimePerPart: 0.2,
        combineParts: true,
        skipOptionalParts: true
      }
    });

    // 第四级：请求延期
    steps.push({
      level: 4,
      description: '建议与老师协商延长截止日期',
      adjustments: {
        extendDeadlineDays: 7,
        combineParts: true,
        skipOptionalParts: true
      }
    });

    return steps.slice(0, Math.max(1, currentLevel));
  }

  // 不足时间处理：应用放松阶梯并生成可行计划
  static handleTimeDeficit(parts: TaskPart[], preferences: any): { adjustedParts: TaskPart[], appliedStep: RelaxationStep } {
    const feasibility = this.checkFeasibility(parts, preferences);
    
    if (feasibility.isFeasible) {
      return { adjustedParts: parts, appliedStep: this.applyRelaxation(parts, preferences, 0)[0] };
    }

    // 根据时间缺口选择合适的放松级别
    const deficitRatio = feasibility.timeDeficit / feasibility.totalTimeRequired;
    let relaxationLevel = 1;
    
    if (deficitRatio > 0.3) relaxationLevel = 2;
    if (deficitRatio > 0.5) relaxationLevel = 3;
    if (deficitRatio > 0.7) relaxationLevel = 4;

    const step = this.applyRelaxation(parts, preferences, relaxationLevel)[relaxationLevel - 1];
    const adjustedParts = this.applyAdjustments(parts, step.adjustments);

    return { adjustedParts, appliedStep: step };
  }

  // ============== 私有方法 ==============

  private static analyzeTaskType(title: string, description: string): string {
    const lowerTitle = title.toLowerCase();
    const lowerDesc = description.toLowerCase();
    
    if (lowerTitle.includes('research') || lowerDesc.includes('literature') || lowerDesc.includes('survey')) {
      return 'research';
    }
    if (lowerTitle.includes('code') || lowerTitle.includes('program') || lowerDesc.includes('implement')) {
      return 'coding';
    }
    if (lowerTitle.includes('write') || lowerTitle.includes('essay') || lowerDesc.includes('report')) {
      return 'writing';
    }
    if (lowerTitle.includes('present') || lowerTitle.includes('demo') || lowerDesc.includes('slide')) {
      return 'presentation';
    }
    return 'generic';
  }

  private static createResearchParts(): TaskPart[] {
    return [
      { id: '1', title: '文献调研', description: '收集和阅读相关文献', estimatedMinutes: 120, priority: 1, dependencies: [], difficulty: 'medium' },
      { id: '2', title: '资料整理', description: '整理和分类收集的资料', estimatedMinutes: 60, priority: 2, dependencies: ['1'], difficulty: 'easy' },
      { id: '3', title: '分析总结', description: '分析资料并撰写总结', estimatedMinutes: 90, priority: 3, dependencies: ['2'], difficulty: 'hard' }
    ];
  }

  private static createCodingParts(): TaskPart[] {
    return [
      { id: '1', title: '环境配置', description: '设置开发环境和工具', estimatedMinutes: 45, priority: 1, dependencies: [], difficulty: 'easy' },
      { id: '2', title: '核心功能', description: '实现主要功能模块', estimatedMinutes: 180, priority: 1, dependencies: ['1'], difficulty: 'hard' },
      { id: '3', title: '测试调试', description: '编写测试和修复bug', estimatedMinutes: 120, priority: 2, dependencies: ['2'], difficulty: 'medium' },
      { id: '4', title: '文档编写', description: '撰写使用文档和注释', estimatedMinutes: 60, priority: 3, dependencies: ['3'], difficulty: 'easy' }
    ];
  }

  private static createWritingParts(): TaskPart[] {
    return [
      { id: '1', title: '大纲制定', description: '规划文章结构和要点', estimatedMinutes: 30, priority: 1, dependencies: [], difficulty: 'easy' },
      { id: '2', title: '初稿撰写', description: '完成文章主要内容', estimatedMinutes: 150, priority: 1, dependencies: ['1'], difficulty: 'medium' },
      { id: '3', title: '修改润色', description: '检查语法和优化表达', estimatedMinutes: 60, priority: 2, dependencies: ['2'], difficulty: 'easy' },
      { id: '4', title: '格式调整', description: '调整格式和引用规范', estimatedMinutes: 30, priority: 3, dependencies: ['3'], difficulty: 'easy' }
    ];
  }

  private static createPresentationParts(): TaskPart[] {
    return [
      { id: '1', title: '内容规划', description: '确定演示内容和结构', estimatedMinutes: 45, priority: 1, dependencies: [], difficulty: 'medium' },
      { id: '2', title: '幻灯片制作', description: '制作演示幻灯片', estimatedMinutes: 120, priority: 1, dependencies: ['1'], difficulty: 'medium' },
      { id: '3', title: '演讲稿', description: '准备演讲内容和备注', estimatedMinutes: 60, priority: 2, dependencies: ['2'], difficulty: 'easy' },
      { id: '4', title: '排练演练', description: '练习演讲和时间控制', estimatedMinutes: 90, priority: 3, dependencies: ['3'], difficulty: 'hard' }
    ];
  }

  private static createGenericParts(): TaskPart[] {
    return [
      { id: '1', title: '准备阶段', description: '理解任务要求和目标', estimatedMinutes: 30, priority: 1, dependencies: [], difficulty: 'easy' },
      { id: '2', title: '执行阶段', description: '完成主要任务内容', estimatedMinutes: 120, priority: 1, dependencies: ['1'], difficulty: 'medium' },
      { id: '3', title: '检查阶段', description: '验证成果和质量', estimatedMinutes: 45, priority: 2, dependencies: ['2'], difficulty: 'easy' }
    ];
  }

  private static adjustPartsByDeadline(parts: TaskPart[], deadline: string): TaskPart[] {
    const daysUntilDeadline = this.calculateDaysUntilDeadline(deadline);
    
    // 如果时间紧张，减少part数量或压缩时间
    if (daysUntilDeadline < 7) {
      return parts.map(part => ({
        ...part,
        estimatedMinutes: Math.max(15, part.estimatedMinutes * 0.8) // 压缩20%时间
      }));
    }
    
    return parts;
  }

  private static calculateDaysUntilDeadline(deadline: string): number {
    const deadlineDate = new Date(deadline);
    const now = new Date();
    const diffMs = deadlineDate.getTime() - now.getTime();
    return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  }

  private static calculateAvailableDays(totalDays: number, avoidDays: string[], weeklyStudyDays: number): number {
    const avoidSet = new Set(avoidDays);
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    let availableDays = 0;
    for (let i = 0; i < totalDays; i++) {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + i);
      const dayName = dayNames[futureDate.getDay()];
      
      if (!avoidSet.has(dayName)) {
        availableDays++;
      }
      
      // 考虑每周学习天数限制
      if (availableDays >= weeklyStudyDays * Math.ceil(totalDays / 7)) {
        break;
      }
    }
    
    return Math.min(availableDays, weeklyStudyDays * Math.ceil(totalDays / 7));
  }

  private static applyAdjustments(parts: TaskPart[], adjustments: any): TaskPart[] {
    let adjustedParts = [...parts];
    
    // 减少每个part的时间
    if (adjustments.reduceTimePerPart) {
      adjustedParts = adjustedParts.map(part => ({
        ...part,
        estimatedMinutes: Math.max(15, part.estimatedMinutes * (1 - adjustments.reduceTimePerPart))
      }));
    }
    
    // 合并简单part
    if (adjustments.combineParts) {
      const easyParts = adjustedParts.filter(p => p.difficulty === 'easy');
      const otherParts = adjustedParts.filter(p => p.difficulty !== 'easy');
      
      if (easyParts.length > 1) {
        const combinedPart: TaskPart = {
          id: 'combined',
          title: '综合任务',
          description: '合并的简单任务',
          estimatedMinutes: easyParts.reduce((sum, p) => sum + p.estimatedMinutes, 0) * 0.8, // 合并后减少20%时间
          priority: Math.min(...easyParts.map(p => p.priority)),
          dependencies: [],
          difficulty: 'easy'
        };
        adjustedParts = [combinedPart, ...otherParts];
      }
    }
    
    // 跳过可选part（优先级低的part）
    if (adjustments.skipOptionalParts) {
      adjustedParts = adjustedParts.filter(p => p.priority <= 2); // 只保留优先级1-2的part
    }
    
    return adjustedParts;
  }
}