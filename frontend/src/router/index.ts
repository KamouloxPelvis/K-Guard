import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import HealthView from '../views/HealthView.vue'
import SecurityView from '../views/SecurityView.vue'

const routes = [
  {
    path: '/',
    component: Dashboard, // Le Dashboard sert de base (Layout)
    children: [
      {
        path: '', // Route par défaut (/)
        name: 'Health',
        component: HealthView
      },
      {
        path: 'security', // Route (/security)
        name: 'Security',
        component: SecurityView
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router