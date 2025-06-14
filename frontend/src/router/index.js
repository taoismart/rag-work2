import { createRouter, createWebHistory } from 'vue-router'
import LoadView from '../views/LoadView.vue'
import ChunkView from '../views/ChunkView.vue'
import ParseView from '../views/ParseView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/load'
    },
    {
      path: '/load',
      name: 'load',
      component: LoadView
    },
    {
      path: '/chunk',
      name: 'chunk',
      component: ChunkView
    },
    {
      path: '/parse',
      name: 'parse',
      component: ParseView
    }
  ]
})

export default router 