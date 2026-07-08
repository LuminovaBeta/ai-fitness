<template>
  <div class="activity-page w-full h-full flex flex-col relative text-white font-sans px-10 py-6">
    
    <header class="flex justify-between items-center mb-8 shrink-0 pl-2">
      <div>
        <h2 class="text-4xl font-bold tracking-tight">运动记录</h2>
        <p class="text-lg text-gray-400 mt-2">回顾训练历程，随时查看分析与建议</p>
      </div>
      
      <div class="flex bg-black/30 p-1.5 rounded-2xl border border-white/10 shadow-inner backdrop-blur-md">
        <button 
          @click="viewMode = 'list'"
          class="flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all duration-300"
          :class="viewMode === 'list' ? 'bg-white/15 shadow-md text-white border border-white/10' : 'text-gray-500 hover:text-gray-300'"
        >
          <List class="w-5 h-5" /> 列表
        </button>
        <button 
          @click="viewMode = 'calendar'"
          class="flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all duration-300"
          :class="viewMode === 'calendar' ? 'bg-white/15 shadow-md text-white border border-white/10' : 'text-gray-500 hover:text-gray-300'"
        >
          <CalendarDays class="w-5 h-5" /> 日历
        </button>
      </div>
    </header>

    <div class="flex-1 flex gap-8 min-h-0">
      
      <div class="w-[35%] flex flex-col h-full overflow-hidden gap-5">
        
        <div class="flex-1 min-h-0">
          <div v-if="isLoading" class="flex justify-center py-20">
            <Loader2 class="w-12 h-12 text-neon-green animate-spin" />
          </div>

          <template v-else>
            <div v-if="viewMode === 'list'" class="flex flex-col gap-4 overflow-y-auto pr-4 custom-scrollbar pb-4 h-full">
            <div 
              v-for="record in activities" :key="record.id"
              @click="selectRecord(record.id)"
              class="p-6 rounded-[2rem] cursor-pointer transition-all duration-300 border shadow-lg group relative overflow-hidden shrink-0"
              :class="selectedRecordId === record.id ? 'bg-white/10 border-neon-green/50' : 'glass-panel hover:bg-white/10 border-white/5'"
            >
              <div v-if="selectedRecordId === record.id" class="absolute inset-0 bg-gradient-to-br from-neon-green/10 to-transparent pointer-events-none"></div>
              
              <div class="flex justify-between items-start mb-5 relative z-10">
                <div class="flex items-center gap-4">
                  <div class="w-14 h-14 rounded-full bg-black/40 flex items-center justify-center text-gray-300 border border-white/5 shadow-inner">
                    <ActivityIcon class="w-6 h-6" />
                  </div>
                  <div>
                    <h4 class="text-xl font-bold tracking-wider">{{ getActivityName(record) }}</h4>
                    <p class="text-sm text-gray-400 mt-1">{{ record.start_time.substring(0, 16) }}</p>
                  </div>
                </div>
                <span class="px-4 py-1.5 rounded-full text-xs font-bold shadow-sm" :class="getIntensityClass(record.intensity)">
                  {{ record.intensity }}
                </span>
              </div>
              
              <div class="grid grid-cols-2 gap-4 relative z-10 bg-black/20 p-4 rounded-2xl border border-white/5">
                <div>
                  <p class="text-gray-500 text-xs tracking-widest mb-1">训练时长</p>
                  <p class="text-2xl font-mono font-bold text-white">
                    {{ record.duration_seconds ? Math.floor(record.duration_seconds / 60) : Math.floor(record.duration / 60) }}<span class="text-xs ml-1 text-gray-400">MIN</span>
                  </p>
                </div>
                <div>
                  <p class="text-gray-500 text-xs tracking-widest mb-1">完成容量</p>
                  <p class="text-2xl font-mono font-bold text-white">{{ record.total_reps }}<span class="text-xs ml-1 text-gray-400">REPS</span></p>
                </div>
              </div>
            </div>
            
            <div v-if="activities.length === 0" class="text-center py-20 text-gray-500 flex flex-col items-center">
              <History class="w-16 h-16 mb-4 opacity-20" />
              <p class="text-xl">暂无训练记录</p>
            </div>
          </div>

            <div v-if="viewMode === 'calendar'" class="flex flex-col h-full glass-panel rounded-[2rem] p-6 shadow-xl border border-white/10 relative overflow-hidden">
                <div class="flex justify-between items-center mb-5 px-1">
                <div>
                  <h3 class="text-2xl font-bold tracking-widest text-white">{{ calendarMonthLabel }}</h3>
                  <p class="text-xs text-gray-300 mt-1">点击日期查看当日详细训练表</p>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    @click="changeCalendarMonth(-1)"
                    class="w-8 h-8 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-gray-300 flex items-center justify-center transition"
                    title="上月"
                  >
                    <ChevronLeft class="w-4 h-4" />
                  </button>
                  <button
                    @click="changeCalendarMonth(1)"
                    class="w-8 h-8 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-gray-300 flex items-center justify-center transition"
                    title="下月"
                  >
                    <ChevronRight class="w-4 h-4" />
                  </button>
                  <span class="text-neon-green font-bold bg-neon-green/10 px-4 py-1 rounded-full border border-neon-green/20 text-sm">
                    {{ activities.length }} 次训练
                  </span>
                </div>
              </div>

              <div class="grid grid-cols-7 gap-2 mb-3 text-center text-gray-300 font-bold text-sm tracking-wider">
                <div v-for="w in ['一','二','三','四','五','六','日']" :key="w">{{ w }}</div>
              </div>

              <div class="grid grid-cols-7 gap-2 mb-4">
                <div
                  v-for="cell in calendarGrid"
                  :key="cell.key"
                  class="aspect-square rounded-xl flex flex-col items-center justify-center relative transition-all duration-200"
                  :class="[
                    !cell.dateKey ? 'opacity-30 cursor-not-allowed' : '',
                    cell.dateKey && cell.count > 0 ? 'cursor-pointer border border-white/10 bg-white/5 hover:bg-white/10' : '',
                    cell.dateKey && cell.count === 0 ? 'cursor-pointer border border-white/5 text-gray-500 hover:bg-white/5' : '',
                    cell.dateKey && selectedCalendarDate === cell.dateKey ? 'bg-neon-green text-black font-black border-neon-green shadow-[0_0_12px_rgba(50,255,126,0.35)]' : ''
                  ]"
                  @click="cell.dateKey ? handleCalendarDayClick(cell) : null"
                >
                  <span class="text-sm z-10">{{ cell.dayNumber || '' }}</span>
                  <span v-if="cell.count > 0" class="text-[10px] mt-1 px-1.5 py-0.5 rounded-full" :class="selectedCalendarDate === cell.dateKey ? 'bg-black/20 text-black' : 'bg-neon-green/20 text-neon-green'">
                    {{ cell.count }} 次
                  </span>
                </div>
              </div>

              <div class="mt-1 rounded-2xl bg-black/25 border border-white/10 p-4 min-h-0 flex-1 flex flex-col">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="text-sm font-bold text-gray-300 tracking-wider">当日训练明细</h4>
                  <span class="text-xs text-gray-400">{{ selectedCalendarDateLabel }}</span>
                </div>
                <div class="overflow-auto custom-scrollbar pr-1 flex-1">
                  <table class="w-full text-xs">
                    <thead class="text-gray-400 border-b border-white/10 sticky top-0 bg-black/70 backdrop-blur">
                      <tr>
                        <th class="text-left py-2">时间</th>
                        <th class="text-left py-2">动作</th>
                        <th class="text-right py-2">次数</th>
                        <th class="text-right py-2">时长</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in selectedDateRecords" :key="item.id" class="border-b border-white/5 hover:bg-white/5 cursor-pointer" @click="selectRecord(item.id)">
                        <td class="py-2">{{ formatRecordTime(item.start_time) }}</td>
                        <td class="py-2">{{ getActivityName(item) }}</td>
                        <td class="py-2 text-right font-mono">{{ item.total_reps }}</td>
                        <td class="py-2 text-right font-mono">{{ formatRecordDuration(item) }}</td>
                      </tr>
                      <tr v-if="selectedDateRecords.length === 0">
                        <td colspan="4" class="py-5 text-center text-gray-300">当天暂无训练记录</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </template>
        </div>

        <div class="shrink-0 rounded-[2rem] bg-black/30 border border-white/10 p-5">
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-2 px-1">
              <MessageSquare class="w-4 h-4 text-ai-start" />
              <span class="text-sm font-bold text-white tracking-widest">向智能教练提问</span>
            </div>
            <button
              @click="openAiChatDialog()"
              class="px-4 py-2 rounded-xl bg-neon-green/15 border border-neon-green/30 text-neon-green text-sm font-semibold hover:bg-neon-green/25 transition-all"
            >
              打开对话框
            </button>
          </div>
          <p class="text-xs text-gray-400 mt-3 px-1">对话仅保存在当前页面内存中，离开页面后自动清空</p>
        </div>
      </div>

      <div class="w-[65%] glass-panel-light rounded-[3rem] flex flex-col relative shadow-2xl p-10 overflow-hidden">
        
        <div class="flex-1 flex flex-col min-h-0">
          
          <div v-if="!selectedRecord" class="flex-1 flex flex-col items-center justify-center text-gray-400 opacity-60">
            <MousePointerClick class="w-20 h-20 mb-8 text-white/20" stroke-width="1" />
            <p class="text-3xl font-bold tracking-widest text-white">请选择一条记录</p>
            <p class="text-xl mt-3">查看详细体征数据与训练复盘报告</p>
          </div>

          <div v-else class="flex flex-col h-full overflow-hidden">
            <div class="flex justify-between items-start pb-6 border-b border-white/10 shrink-0">
              <div>
                <h3 class="text-3xl font-bold tracking-tight mb-3 flex items-center gap-4">
                  {{ getActivityName(selectedRecord) }}
                  <span class="text-sm px-4 py-1.5 bg-white/10 rounded-full font-normal border border-white/10 tracking-wider">
                    {{ selectedRecord.training_mode }}
                  </span>
                </h3>
                <p class="text-gray-400 text-base">{{ selectedRecord.start_time }}</p>
              </div>
              <div class="flex gap-4">
                <div class="text-center bg-black/20 px-5 py-3 rounded-2xl border border-white/5 shadow-inner">
                  <p class="text-gray-300 text-xs tracking-widest mb-1">RPE 疲劳度</p>
                  <p class="text-3xl font-mono text-white">{{ selectedRecord.perceived_exertion || '-' }}<span class="text-sm text-gray-500 ml-1">/10</span></p>
                </div>
                <div class="text-center bg-black/20 px-5 py-3 rounded-2xl border border-white/5 shadow-inner">
                  <p class="text-gray-300 text-xs tracking-widest mb-1">动作评分</p>
                  <p class="text-3xl font-mono text-neon-green font-bold">{{ selectedRecord.quality_score || '-' }}<span class="text-sm text-gray-500 ml-1">分</span></p>
                </div>
              </div>
            </div>

            <div class="flex-1 overflow-y-auto custom-scrollbar pr-4 mt-6 flex flex-col gap-6 pb-2 relative">
              <div v-if="isDetailLoading" class="absolute top-2 right-2 z-20 pointer-events-none">
                <div class="flex items-center gap-2 text-sm text-gray-200 bg-black/50 px-4 py-2 rounded-full border border-white/10 shadow-lg backdrop-blur-sm">
                  <Loader2 class="w-4 h-4 animate-spin" />
                  加载详情中
                </div>
              </div>
              
              <div v-if="selectedRecord.ai_report" class="p-8 rounded-[2rem] bg-gradient-to-br from-ai-start/20 to-ai-end/20 border border-ai-start/30 relative overflow-hidden shadow-lg shrink-0">
                <div class="absolute -top-4 -right-4 p-4 opacity-10 pointer-events-none">
                  <Sparkles class="w-48 h-48" />
                </div>
                <h4 class="text-xl font-bold text-white mb-4 flex items-center gap-3 relative z-10">
                  <Sparkles class="w-5 h-5 text-neon-green" /> 训练评估
                </h4>
                <p class="text-gray-200 leading-relaxed text-lg relative z-10 tracking-wide">
                  {{ selectedRecord.ai_report.feedback }}
                </p>
                <div class="mt-6 pt-6 border-t border-white/10 relative z-10 bg-black/10 -mx-8 -mb-8 px-8 py-6">
                  <p class="text-neon-orange font-bold text-base"><span class="text-gray-400 font-medium mr-2">指导建议：</span>{{ selectedRecord.ai_report.suggestion }}</p>
                </div>
              </div>

              <div class="rounded-[2rem] bg-black/30 border border-white/5 flex flex-col p-6 shrink-0 shadow-inner">
                <div class="flex justify-between items-center mb-6">
                   <h4 class="text-lg font-bold text-white flex items-center gap-2">
                     <HeartPulse class="w-5 h-5 text-neon-red" /> 生理体征曲线
                   </h4>
                   <p class="text-sm text-gray-300">共采集 {{ selectedRecord.sensor_data_series?.length || 0 }} 组关键数据</p>
                </div>
                
                <div v-if="selectedRecord.sensor_data_series && selectedRecord.sensor_data_series.length > 0" class="flex gap-6 mb-6">
                   <div class="flex-1 bg-white/5 p-4 rounded-xl border border-white/5 flex justify-between items-center">
                      <span class="text-gray-400 font-medium">平均心率</span>
                      <p class="text-2xl font-mono text-neon-red font-bold">
                        {{ Math.round(selectedRecord.sensor_data_series.reduce((sum, item) => sum + item.heart_rate, 0) / selectedRecord.sensor_data_series.length) }}
                        <span class="text-sm text-gray-300 font-normal">bpm</span>
                      </p>
                   </div>
                   <div class="flex-1 bg-white/5 p-4 rounded-xl border border-white/5 flex justify-between items-center">
                      <span class="text-gray-400 font-medium">平均血氧</span>
                      <p class="text-2xl font-mono text-neon-green font-bold">
                        {{ (selectedRecord.sensor_data_series.reduce((sum, item) => sum + item.spo2, 0) / selectedRecord.sensor_data_series.length).toFixed(1) }}
                        <span class="text-sm text-gray-300 font-normal">%</span>
                      </p>
                   </div>
                </div>
                
                <div class="w-full h-[280px] bg-black/20 rounded-xl relative border border-white/5 overflow-hidden">
                  <div ref="chartRef" class="absolute inset-0"></div>
                  <div v-if="!selectedRecord.sensor_data_series || selectedRecord.sensor_data_series.length === 0" class="absolute inset-0 flex flex-col items-center justify-center bg-black/35 z-10 pointer-events-none">
                    <ActivityIcon class="w-10 h-10 text-gray-600 mb-2 opacity-50" stroke-width="1.5" />
                    <p class="text-sm text-gray-300">本次训练未采集到体征序列数据</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <div
      v-if="isAiChatDialogOpen"
      class="fixed inset-0 z-[80] bg-black/70 backdrop-blur-sm flex items-center justify-center p-6"
      @click.self="closeAiChatDialog"
    >
      <div class="w-[980px] max-w-[92vw] h-[76vh] rounded-[2rem] border border-white/15 bg-[#101318]/95 shadow-[0_30px_80px_rgba(0,0,0,.6)] p-6 flex flex-col">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-2xl font-bold">智能教练对话</h3>
            <p class="text-xs text-gray-400 mt-1">会话仅保存在内存，不落库</p>
          </div>
          <button @click="closeAiChatDialog" class="w-10 h-10 rounded-full border border-white/15 bg-white/5 hover:bg-white/10 transition-all">✕</button>
        </div>

        <div class="flex gap-2 mb-3 overflow-x-auto pb-1 custom-scrollbar">
          <button
            v-for="(chip, idx) in quickQuestions" :key="idx"
            @click="sendAiMessage(chip)"
            class="whitespace-nowrap px-3 py-2 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-gray-300 hover:bg-white/10 hover:text-white transition-all shadow-sm"
          >
            {{ chip }}
          </button>
        </div>

        <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar pr-2 space-y-3">
          <div v-if="chatMessages.length === 0" class="h-full flex items-center justify-center text-gray-500 text-sm">
            还没有对话，输入问题开始。
          </div>
          <div
            v-for="(msg, idx) in chatMessages"
            :key="idx"
            class="rounded-2xl px-4 py-3 border"
            :class="msg.role === 'user' ? 'ml-20 bg-white/5 border-white/10' : 'mr-20 bg-neon-green/10 border-neon-green/30'"
          >
            <p class="text-[11px] uppercase tracking-wider mb-1" :class="msg.role === 'user' ? 'text-gray-400' : 'text-neon-green'">
              {{ msg.role === 'user' ? '你' : '智能教练' }}
            </p>
            <p v-if="msg.role === 'user'" class="text-sm leading-6 whitespace-pre-wrap break-words">{{ msg.content }}</p>
            <div
              v-else
              class="text-sm leading-6 break-words markdown-body"
              v-html="renderAssistantMarkdown(msg.content)"
            ></div>
          </div>
        </div>

        <div class="pt-4 mt-4 border-t border-white/10">
          <div class="relative flex items-center">
            <div class="absolute left-4 w-8 h-8 rounded-full bg-gradient-to-tr from-ai-start to-ai-end flex items-center justify-center shadow-lg pointer-events-none">
              <Mic class="w-4 h-4 text-white" />
            </div>
            <input
              v-model="chatInput"
              @keyup.enter="sendAiMessage(chatInput)"
              type="text"
              placeholder="输入你的问题"
              class="w-full h-12 bg-black/50 border border-white/10 rounded-full pl-14 pr-14 text-sm text-white outline-none focus:border-neon-green/50 transition-all shadow-inner placeholder-gray-500"
              :disabled="isChatting"
            >
            <button
              @click="sendAiMessage(chatInput)"
              :disabled="!chatInput || isChatting"
              class="absolute right-2 w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 shadow-md"
              :class="chatInput && !isChatting ? 'bg-neon-green text-black hover:scale-105' : 'bg-white/10 text-gray-500'"
            >
              <Loader2 v-if="isChatting" class="w-4 h-4 animate-spin" />
              <Send v-else class="w-4 h-4 ml-0.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch, inject } from 'vue'
import { List, CalendarDays, MousePointerClick, Activity as ActivityIcon, Sparkles, Mic, Send, Loader2, HeartPulse, History, MessageSquare, ChevronLeft, ChevronRight } from '@lucide/vue'
import * as echarts from 'echarts' // 引入 ECharts
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { fetchUserActivities, fetchUserActivityDetail } from '../api/user'
import { askAi } from '../api/chat'

const speakWithBackendTts = inject('speakWithBackendTts')
const stopVoice = inject('stopVoice')

const viewMode = ref('list')
const isLoading = ref(false)
const activities = ref([])
const selectedRecordId = ref(null)
const selectedRecord = ref(null)
const selectedCalendarDate = ref('')
const calendarCursor = ref('')
const isDetailLoading = ref(false)

const chatInput = ref('')
const isChatting = ref(false)
const isAiChatDialogOpen = ref(false)
const chatMessages = ref([])
const quickQuestions = [
  "总结本周的训练表现", 
  "评估我的心率恢复能力", 
  "基于近期负荷推荐下次计划"
]

marked.setOptions({
  breaks: true,
  gfm: true
})

const renderAssistantMarkdown = (text) => {
  const raw = String(text || '')
  const html = marked.parse(raw)
  return DOMPurify.sanitize(String(html))
}

const openAiChatDialog = (presetQuestion = '') => {
  isAiChatDialogOpen.value = true
  if (presetQuestion) {
    sendAiMessage(presetQuestion)
  }
}

const closeAiChatDialog = () => {
  if (stopVoice) {
    stopVoice()
  }
  isAiChatDialogOpen.value = false
}

const getIntensityClass = (intensity) => {
  if (intensity === '高强度' || intensity === 'HIGH') return 'bg-neon-red/20 text-neon-red border border-neon-red/30'
  if (intensity === '中强度' || intensity === 'MED') return 'bg-neon-orange/20 text-neon-orange border border-neon-orange/30'
  return 'bg-neon-green/20 text-neon-green border border-neon-green/30'
}

const activityNameFallback = {
  squat: '深蹲',
  jumping_jack: '开合跳',
  push_up: '俯卧撑',
  pushup: '俯卧撑',
  plank: '平板支撑',
  lunge: '弓箭步',
  mixed_plan: '混合计划'
}

const getActivityName = (record) => {
  const code = String(record?.activity_type || '').trim()
  const name = String(record?.activity_name || '').trim()
  if (name) return name
  return activityNameFallback[code] || code || '-'
}

const parseRecordDate = (startTime) => {
  const raw = String(startTime || '').trim().replace(' ', 'T')
  const dt = new Date(raw)
  if (Number.isNaN(dt.getTime())) return null
  return dt
}

const toDateKey = (dt) => {
  if (!dt) return ''
  const y = dt.getFullYear()
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const d = String(dt.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const toMonthKey = (dt) => {
  if (!dt) return ''
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}`
}

const parseMonthKey = (monthKey) => {
  const text = String(monthKey || '')
  const m = text.match(/^(\d{4})-(\d{2})$/)
  if (!m) return null
  return new Date(Number(m[1]), Number(m[2]) - 1, 1)
}

const activitiesByDate = computed(() => {
  const map = {}
  for (const act of activities.value) {
    const dt = parseRecordDate(act.start_time)
    if (!dt) continue
    const key = toDateKey(dt)
    if (!map[key]) map[key] = []
    map[key].push(act)
  }
  Object.values(map).forEach((list) => {
    list.sort((a, b) => String(b.start_time || '').localeCompare(String(a.start_time || '')))
  })
  return map
})

const calendarBaseDate = computed(() => {
  if (calendarCursor.value) {
    const fromCursor = parseMonthKey(calendarCursor.value)
    if (fromCursor) return fromCursor
  }
  if (selectedCalendarDate.value) {
    const dt = parseRecordDate(`${selectedCalendarDate.value} 00:00:00`)
    if (dt) return dt
  }
  const firstRecord = activities.value[0]
  const dt = parseRecordDate(firstRecord?.start_time)
  return dt || new Date()
})

const calendarMonthLabel = computed(() => {
  const base = calendarBaseDate.value
  const year = base.getFullYear()
  const month = base.getMonth() + 1
  return `${year}年${month}月`
})

const calendarGrid = computed(() => {
  const base = calendarBaseDate.value
  const year = base.getFullYear()
  const month = base.getMonth()

  const firstDay = new Date(year, month, 1)
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const firstWeekday = (firstDay.getDay() + 6) % 7 // 周一=0

  const cells = []
  for (let i = 0; i < firstWeekday; i++) {
    cells.push({ key: `blank-${i}`, dateKey: '', dayNumber: '', count: 0 })
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const dt = new Date(year, month, day)
    const dateKey = toDateKey(dt)
    const count = (activitiesByDate.value[dateKey] || []).length
    cells.push({
      key: dateKey,
      dateKey,
      dayNumber: day,
      count
    })
  }

  while (cells.length % 7 !== 0) {
    const idx = cells.length
    cells.push({ key: `blank-tail-${idx}`, dateKey: '', dayNumber: '', count: 0 })
  }

  return cells
})

const selectedDateRecords = computed(() => {
  if (!selectedCalendarDate.value) return []
  return activitiesByDate.value[selectedCalendarDate.value] || []
})

const selectedCalendarDateLabel = computed(() => {
  if (!selectedCalendarDate.value) return '未选择日期'
  return selectedCalendarDate.value
})

const formatRecordTime = (startTime) => {
  const dt = parseRecordDate(startTime)
  if (!dt) return '--:--'
  return `${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}`
}

const formatRecordDuration = (record) => {
  const sec = Number(record?.duration_seconds ?? record?.duration ?? 0)
  if (!Number.isFinite(sec) || sec <= 0) return '0分'
  const min = Math.floor(sec / 60)
  const rem = sec % 60
  if (min <= 0) return `${rem}秒`
  return rem > 0 ? `${min}分${rem}秒` : `${min}分`
}

const handleCalendarDayClick = (cell) => {
  const key = String(cell?.dateKey || '')
  if (!key) return
  selectedCalendarDate.value = key
  const picked = parseRecordDate(`${key} 00:00:00`)
  calendarCursor.value = toMonthKey(picked)
  const records = activitiesByDate.value[key] || []
  if (records.length > 0) {
    selectRecord(records[0].id)
  }
}

const changeCalendarMonth = (delta) => {
  const base = calendarBaseDate.value
  const moved = new Date(base.getFullYear(), base.getMonth() + delta, 1)
  calendarCursor.value = toMonthKey(moved)
}

const fetchActivities = async () => {
  isLoading.value = true
  try {
    const data = await fetchUserActivities()
    activities.value = data.records || []
    if (!selectedCalendarDate.value && activities.value.length > 0) {
      const firstDate = parseRecordDate(activities.value[0].start_time)
      selectedCalendarDate.value = toDateKey(firstDate)
      calendarCursor.value = toMonthKey(firstDate)
    }
    if (!selectedRecordId.value && activities.value.length > 0) {
      selectRecord(activities.value[0].id)
    }
  } catch (err) {
    console.error('获取记录失败', err)
  } finally {
    isLoading.value = false
  }
}

// ================= ECharts 相关逻辑 =================
const chartRef = ref(null)
let chartInstance = null
let selectRecordReqSeq = 0

// 当选中的记录发生变化且包含体征数据时，渲染图表
watch(selectedRecord, async (newVal) => {
  if (newVal && newVal.sensor_data_series && newVal.sensor_data_series.length > 0) {
    await nextTick() // 等待 DOM 更新挂载 chartRef
    renderChart(newVal.sensor_data_series)
  } else {
    // 如果没有数据，销毁历史图表实例
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }
  }
})

const renderChart = (seriesData) => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  // 数据映射解析
  const xAxisData = seriesData.map(item => `${item.offset}s`)
  const hrData = seriesData.map(item => item.heart_rate)
  const spo2Data = seriesData.map(item => item.spo2)

  const option = {
    // 深色模式网格设定
    grid: { top: 40, right: 50, bottom: 20, left: 50, containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(12, 12, 14, 0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff', fontSize: 16 },
      padding: [12, 16],
      formatter: function (params) {
        const dataIndex = params[0].dataIndex
        const phase = seriesData[dataIndex].phase
        const reps = seriesData[dataIndex].current_rep
        let tip = `<div style="font-weight:bold;margin-bottom:8px;">${params[0].axisValue} - ${phase} <span style="font-size:12px;color:#aaa">(第${reps}次)</span></div>`
        params.forEach(p => {
          tip += `${p.marker} <span style="color:#ddd">${p.seriesName}:</span> <strong style="color:${p.color}">${p.value}</strong><br/>`
        })
        return tip
      }
    },
    legend: {
      data: ['心率 (BPM)', '血氧 (%)'],
      textStyle: { color: '#888', fontSize: 14 },
      top: 0
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: '#888', margin: 12 }
    },
    // 双 Y 轴设计
    yAxis: [
      {
        type: 'value',
        name: '心率',
        min: 60,
        max: 200, // 运动心率合理区间
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
        axisLabel: { color: '#FF4D4D', fontWeight: 'bold' },
        nameTextStyle: { color: '#FF4D4D', padding: [0, 20, 0, 0] }
      },
      {
        type: 'value',
        name: '血氧',
        min: 90,
        max: 100, // 血氧合理区间
        splitLine: { show: false }, // 隐藏第二条分割线防止网格杂乱
        axisLabel: { color: '#32FF7E', fontWeight: 'bold' },
        nameTextStyle: { color: '#32FF7E', padding: [0, 0, 0, 20] }
      }
    ],
    series: [
      {
        name: '心率 (BPM)',
        type: 'line',
        yAxisIndex: 0,
        data: hrData,
        smooth: true,
        symbolSize: 8,
        itemStyle: { color: '#FF4D4D' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255,77,77,0.3)' },
            { offset: 1, color: 'rgba(255,77,77,0)' }
          ])
        }
      },
      {
        name: '血氧 (%)',
        type: 'line',
        yAxisIndex: 1,
        data: spo2Data,
        smooth: true,
        symbolSize: 8,
        itemStyle: { color: '#32FF7E' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(50,255,126,0.3)' },
            { offset: 1, color: 'rgba(50,255,126,0)' }
          ])
        }
      }
    ]
  }
  chartInstance.setOption(option)
}

// 监听窗口尺寸变化，自适应重绘图表
const handleResize = () => {
  if (chartInstance) chartInstance.resize()
}
// ================= ECharts 逻辑结束 =================

const selectRecord = async (id) => {
  if(!id) return
  const reqSeq = ++selectRecordReqSeq
  selectedRecordId.value = id
  isDetailLoading.value = true
  try {
    const detail = await fetchUserActivityDetail(id)
    if (reqSeq !== selectRecordReqSeq) return
    selectedRecord.value = detail
  } catch (err) {
    console.error('获取详情失败', err)
  } finally {
    if (reqSeq === selectRecordReqSeq) {
      isDetailLoading.value = false
    }
  }
}

const sendAiMessage = async (message) => {
  if (!message || isChatting.value) return
  
  const textToSend = String(message).trim()
  if (!textToSend) return

  chatInput.value = ''
  isChatting.value = true
  chatMessages.value.push({ role: 'user', content: textToSend })
  
  try {
    const data = await askAi(textToSend)
    const messageText = String(data?.reply || data?.spoken_text || data?.tts_text || '').trim() || '暂时没有可用回复'
    const ttsText = String(data?.tts_text || data?.reply || data?.spoken_text || '').trim() || messageText
    chatMessages.value.push({ role: 'assistant', content: messageText })
    if (speakWithBackendTts) {
      await speakWithBackendTts(ttsText)
    }
  } catch (err) {
    console.error('Chat 失败', err)
    chatMessages.value.push({ role: 'assistant', content: '请求失败，请稍后重试。' })
  } finally {
    isChatting.value = false
  }
}

watch(viewMode, (mode) => {
  if (mode !== 'calendar') return
  if (!selectedCalendarDate.value && activities.value.length > 0) {
    const firstDate = parseRecordDate(activities.value[0].start_time)
    selectedCalendarDate.value = toDateKey(firstDate)
  }
})

onMounted(() => {
  fetchActivities()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) chartInstance.dispose()
})
</script>

<style scoped>
.activity-page {
  color: #fff;
  font-family: "SF Pro Display", Inter, system-ui, sans-serif;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}

.markdown-body :deep(p) {
  margin: 0.2rem 0;
}

.markdown-body :deep(pre) {
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.75rem;
  padding: 0.75rem;
  overflow-x: auto;
}

.markdown-body :deep(code) {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 0.35rem;
  padding: 0.1rem 0.35rem;
  font-size: 0.85em;
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.35rem 0;
  padding-left: 1.1rem;
}

.markdown-body :deep(li + li) {
  margin-top: 0.2rem;
}

.markdown-body :deep(a) {
  color: #79f8b1;
  text-decoration: underline;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid rgba(50, 255, 126, 0.45);
  padding-left: 0.65rem;
  color: rgba(255, 255, 255, 0.85);
  margin: 0.35rem 0;
}
</style>