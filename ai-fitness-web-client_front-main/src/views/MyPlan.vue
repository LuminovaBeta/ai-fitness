<template>
  <div class="w-full h-full p-8 flex flex-col gap-6 text-white">
    <header class="shrink-0 flex items-end justify-between gap-4">
      <div>
        <h2 class="text-4xl font-bold tracking-tight">我的计划</h2>
        <p class="text-gray-400 mt-2">查看当前 7 天训练安排，并支持一键重新生成</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/profile')"
          class="h-11 px-5 rounded-xl border border-white/15 bg-white/5 hover:bg-white/10 transition-all"
        >
          返回我页面
        </button>
        <button
          @click="regeneratePlan"
          :disabled="isRegenerating"
          class="h-11 px-5 rounded-xl font-semibold transition-all"
          :class="isRegenerating ? 'bg-white/5 text-gray-500 border border-white/10 cursor-not-allowed' : 'btn-neon-primary'"
        >
          {{ isRegenerating ? '重新生成中...' : '重新生成计划' }}
        </button>
      </div>
    </header>

    <div v-if="statusMessage.text" class="px-5 py-3 rounded-xl border" :class="statusClass">
      {{ statusMessage.text }}
    </div>

    <section class="glass-panel-light rounded-[2rem] p-6 flex-1 min-h-0 flex flex-col">
      <div class="flex items-center justify-between mb-5">
        <div>
          <h3 class="text-2xl font-bold tracking-wider">当前执行计划</h3>
          <p class="text-sm text-gray-400 mt-1">共 {{ planDays.length }} / 7 天</p>
        </div>
        <p class="text-sm text-gray-400">生成日期：{{ createdAtText }}</p>
      </div>

      <div v-if="isLoading" class="flex-1 flex items-center justify-center text-gray-400">
        正在加载训练计划...
      </div>

      <div v-else-if="planDays.length === 0" class="flex-1 flex flex-col items-center justify-center text-gray-400">
        <span class="text-6xl mb-4">📭</span>
        <p class="text-2xl font-bold">当前暂无可用计划</p>
        <p class="text-sm mt-2">点击右上角重新生成计划即可创建新的 7 天安排</p>
      </div>

      <div v-else class="flex-1 overflow-y-auto pr-2 grid grid-cols-2 gap-4 auto-rows-max">
        <article
          v-for="day in normalizedPlan"
          :key="day.day"
          class="rounded-2xl border border-white/10 bg-black/20 p-5"
        >
          <div class="flex items-center justify-between mb-4">
            <h4 class="text-xl font-bold">第 {{ day.day }} 天</h4>
            <span class="text-xs px-3 py-1 rounded-full border" :class="day.exercises.length === 0 ? 'text-neon-orange border-neon-orange/30 bg-neon-orange/10' : 'text-neon-green border-neon-green/30 bg-neon-green/10'">
              {{ day.exercises.length === 0 ? '休息日' : `${day.exercises.length} 个动作` }}
            </span>
          </div>

          <div v-if="day.exercises.length === 0" class="rounded-xl border border-dashed border-white/10 bg-white/5 px-4 py-5 text-gray-400 text-sm">
            今日建议恢复与拉伸，暂不安排主训练动作。
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="(exercise, index) in day.exercises"
              :key="`${day.day}-${index}-${exercise.type}`"
              class="rounded-xl border border-white/8 bg-white/5 px-4 py-4"
            >
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-lg font-semibold">{{ getExerciseName(exercise.type) }}</p>
                  <p class="text-xs text-gray-400 mt-1">训练项目已就绪</p>
                </div>
                <div class="text-right text-sm text-gray-300">
                  <p>{{ exercise.sets || 0 }} 组</p>
                  <p>{{ exercise.reps_per_set || 0 }} 次/组</p>
                  <p>休息 {{ exercise.rest_sec || 0 }} 秒</p>
                </div>
              </div>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCurrentPlan, fetchUserProfile } from '../api/user'
import { fetchExercises, initGeneratePlan } from '../api/train'

const router = useRouter()

const isLoading = ref(false)
const isRegenerating = ref(false)
const createdAtText = ref('--')
const planDays = ref([])
const profile = ref({ goal: '提升耐力' })
const exerciseDict = ref({})
const statusMessage = ref({ type: 'ok', text: '' })

const statusClass = computed(() => {
  if (statusMessage.value.type === 'error') return 'border-neon-red/30 bg-neon-red/10 text-neon-red'
  if (statusMessage.value.type === 'warning') return 'border-neon-orange/30 bg-neon-orange/10 text-neon-orange'
  return 'border-neon-green/30 bg-neon-green/10 text-neon-green'
})

const normalizedPlan = computed(() => {
  return [...planDays.value]
    .filter(item => item && typeof item === 'object')
    .sort((a, b) => Number(a.day || 0) - Number(b.day || 0))
})

const loadExerciseDict = async () => {
  try {
    const data = await fetchExercises()
    const dict = {}
    const list = Array.isArray(data?.exercises) ? data.exercises : []
    for (const item of list) {
      const code = String(item?.code || '').trim()
      if (!code) continue
      dict[code] = item?.name_zh || item?.name || code
    }
    exerciseDict.value = dict
  } catch {
    exerciseDict.value = {}
  }
}

const getExerciseName = (type) => {
  return exerciseDict.value[type] || type || '未命名动作'
}

const loadProfile = async () => {
  try {
    const data = await fetchUserProfile()
    profile.value = {
      ...data,
      goal: data?.goal || data?.target || '提升耐力'
    }
  } catch {
    profile.value = { goal: '提升耐力' }
  }
}

const loadPlan = async () => {
  isLoading.value = true
  try {
    const data = await fetchCurrentPlan()
    planDays.value = Array.isArray(data?.plan_content) ? data.plan_content : []
    createdAtText.value = data?.created_at || '--'
    statusMessage.value = { type: 'ok', text: planDays.value.length ? '已加载当前计划' : '当前暂无训练计划' }
  } catch (error) {
    planDays.value = []
    createdAtText.value = '--'
    statusMessage.value = { type: 'warning', text: error?.status === 404 ? '当前暂无训练计划，请重新生成' : '读取计划失败，请稍后重试' }
  } finally {
    isLoading.value = false
  }
}

const regeneratePlan = async () => {
  if (isRegenerating.value) return
  isRegenerating.value = true
  statusMessage.value = { type: 'ok', text: '正在重新整理你的训练计划...' }
  try {
    await initGeneratePlan({ goal: profile.value?.goal || '提升耐力' })
    await loadPlan()
    statusMessage.value = { type: 'ok', text: '训练计划已重新生成' }
  } catch {
    statusMessage.value = { type: 'error', text: '重新生成失败，请稍后再试' }
  } finally {
    isRegenerating.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadExerciseDict(), loadProfile(), loadPlan()])
})
</script>