with open('src/views/Home.vue', 'r') as f:
    content = f.read()

old = '<div class="min-w-0 flex-1">{{ v.name }}</div>\n                  </div>\n                </div>\n                <div v-else-if="videoSearched"'

# Check
idx = content.find('v.name')
print('Context:', repr(content[idx-50:idx+100]))

if old in content:
    print('FOUND old')
else:
    # Try with different indentation
    old2 = '<div class="min-w-0 flex-1">{{ v.name }}</div>\n                 </div>\n               </div>\n               <div v-else-if="videoSearched"'
    if old2 in content:
        print('FOUND old2')
        new2 = '<div class="min-w-0 flex-1">{{ v.name }}</div>\n                    <button @click.stop="playVideo(v)" class="text-xs px-1.5 py-0.5 rounded bg-zinc-200 dark:bg-zinc-700 hover:bg-blue-100 dark:hover:bg-blue-900/50 text-zinc-600 dark:text-zinc-300" title="播放">\u25b6</button>\n                  </div>\n                  <div v-if="selectedVideoIndex !== null" class="mt-2 pt-2 border-t border-zinc-200 dark:border-zinc-600">\n                    <button\n                      @click="fetchSoundbiteAlignment"\n                      :disabled="asrAligning"\n                      class="text-xs px-3 py-1.5 rounded bg-green-600 hover:bg-green-700 disabled:bg-zinc-400 text-white font-medium transition-colors"\n                    >\n                      {{ asrAligning ? \'ASR\u5bf9\u9f50\u4e2d...\' : \'\u83b7\u53d6\u540c\u671f\u58f0\u97f3\u9891\u4f4d\u7f6e\' }}\n                    </button>\n                    <div v-if="asrResults.length > 0" class="mt-2 space-y-1">\n                      <div v-for="(seg, si) in asrResults" :key="si" class="flex items-center gap-2 text-xs p-1.5 rounded bg-green-50 dark:bg-green-900/20">\n                        <span class="text-green-700 dark:text-green-400 font-mono">{{ formatTime(seg.start_time) }} - {{ formatTime(seg.end_time) }}</span>\n                        <span v-if="seg.confidence > 0" class="text-zinc-400">\u7f6e\u4fe1\u5ea6 {{ (seg.confidence * 100).toFixed(0) }}%</span>\n                        <span v-else class="text-red-400">\u672a\u5339\u914d</span>\n                      </div>\n                    </div>\n                  </div>\n                </div>\n                <div v-else-if="videoSearched"'
        content = content.replace(old2, new2, 1)
        with open('src/views/Home.vue', 'w') as f:
            f.write(content)
        print('REPLACED')
    else:
        print('STILL NOT FOUND')
