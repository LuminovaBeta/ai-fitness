<template>
  <div class="w-full h-full p-8 text-white flex flex-col gap-6">
    <header class="shrink-0 flex items-center justify-between">
      <div>
        <h2 class="text-4xl font-bold tracking-tight">自由训练设置</h2>
        <p class="text-gray-400 mt-2">选择动作并设定组数、次数与休息时间</p>
      </div>
      <button
        @click="startTraining"
        :disabled="isSubmitting"
        class="px-8 py-4 rounded-2xl btn-neon-primary font-bold text-xl"
      >
        {{ isSubmitting ? '启动中...' : '开始训练' }}
      </button>
    </header>

    <section class="grid grid-cols-12 gap-6 flex-1 min-h-0">
      <div class="col-span-8 glass-panel rounded-[2rem] p-6 flex flex-col min-h-0">
        <h3 class="text-2xl font-bold mb-4">动作选择</h3>
        <div class="grid grid-cols-3 gap-4 overflow-y-auto pr-2">
          <button
            v-for="item in exerciseOptions"
            :key="item.value"
            @click="toggleExercise(item.value)"
            class="h-28 rounded-2xl border transition-all text-left px-4"
            :class="selectedExercises.includes(item.value)
              ? 'bg-neon-green/20 border-neon-green text-neon-green'
              : 'bg-white/5 border-white/10 hover:bg-white/10 text-white'"
          >
            <p class="text-lg font-bold">{{ item.label }}</p>
            <p class="text-sm mt-2 text-gray-400">{{ item.desc }}</p>
          </button>
        </div>
      </div>

      <div class="col-span-4 glass-panel-light rounded-[2rem] p-6 flex flex-col gap-4">
        <h3 class="text-2xl font-bold">训练参数</h3>

        <label class="text-sm text-gray-400">组数</label>
        <input v-model.number="form.sets" type="number" min="1" max="10" class="h-14 rounded-xl bg-black/30 border border-white/10 px-4 text-xl" />

        <label class="text-sm text-gray-400">每组次数</label>
        <input v-model.number="form.reps" type="number" min="1" max="100" class="h-14 rounded-xl bg-black/30 border border-white/10 px-4 text-xl" />

        <label class="text-sm text-gray-400">组间休息（秒）</label>
        <input v-model.number="form.restSeconds" type="number" min="10" max="300" class="h-14 rounded-xl bg-black/30 border border-white/10 px-4 text-xl" />

        <div class="mt-auto rounded-xl bg-black/30 border border-white/10 p-4 text-sm text-gray-300">
          已选动作：{{ selectedExercises.length }} 项
        </div>

        <p class="text-sm" :class="status.type === 'error' ? 'text-neon-red' : 'text-neon-green'">
          {{ status.text }}
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchExercises, startTrainSession } from '../api/train'

const router = useRouter()

const exerciseOptions = ref([])

const selectedExercises = ref([])

const form = reactive({
  sets: 3,
  reps: 12,
  restSeconds: 45
})

const isSubmitting = ref(false)
const status = reactive({
  type: 'ok',
  text: '请选择动作并设定参数'
})

const toggleExercise = (value) => {
  if (selectedExercises.value.includes(value)) {
    selectedExercises.value = selectedExercises.value.filter((i) => i !== value)
    return
  }
  selectedExercises.value.push(value)
}

const startTraining = async () => {
  if (exerciseOptions.value.length === 0) {
    status.type = 'error'
    status.text = '当前还没有可用训练动作，请稍后再试'
    return
  }

  if (selectedExercises.value.length === 0) {
    status.type = 'error'
    status.text = '请至少选择一个动作'
    return
  }

  const normalizedSets = Math.max(1, Math.min(10, Number(form.sets) || 1))
  const normalizedReps = Math.max(1, Math.min(100, Number(form.reps) || 1))
  const normalizedRestSeconds = Math.max(10, Math.min(300, Number(form.restSeconds) || 30))

  form.sets = normalizedSets
  form.reps = normalizedReps
  form.restSeconds = normalizedRestSeconds

  isSubmitting.value = true
  const payload = {
    mode: 'free',
    exercises: selectedExercises.value,
    sets: normalizedSets,
    reps: normalizedReps,
    reps_per_set: normalizedReps,
    restSec: normalizedRestSeconds,
    rest_sec: normalizedRestSeconds,
    rest_seconds: normalizedRestSeconds,
    intensity: 'medium'
  }

  try {
    const data = await startTrainSession(payload)
    status.type = 'ok'
    status.text = '训练已创建，正在进入训练页'

    router.push({
      path: '/training-session',
      query: {
        sessionId: data.session_id || data.id || '',
        sets: String(normalizedSets),
        reps: String(normalizedReps),
        restSec: String(normalizedRestSeconds),
        exercise: selectedExercises.value[0] || '',
        exercises: selectedExercises.value.join(',')
      }
    })
  } catch (error) {
    status.type = 'error'
    status.text = '启动失败，请稍后重试'
  } finally {
    isSubmitting.value = false
  }
}

const hydrateExercises = async () => {
  try {
    const data = await fetchExercises()
    if (!Array.isArray(data.exercises) || data.exercises.length === 0) {
      exerciseOptions.value = []
      selectedExercises.value = []
      status.type = 'error'
      status.text = '暂未检测到可用动作，请稍后再试'
      return
    }

    exerciseOptions.value = data.exercises.map((item) => ({
      value: item.code,
      label: item.name_zh || item.name || item.code,
      desc: item.desc || '标准训练动作'
    }))

    selectedExercises.value = [exerciseOptions.value[0].value]
    status.type = 'ok'
    status.text = `已加载 ${exerciseOptions.value.length} 个训练动作`
  } catch (error) {
    exerciseOptions.value = []
    selectedExercises.value = []
    status.type = 'error'
    status.text = '动作列表加载失败，请稍后重试'
  }
}

onMounted(() => {
  hydrateExercises()
})
</script>
