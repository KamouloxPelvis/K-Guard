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
        meta: { requiresAuth: true },
        component: HealthView,
      },
      {
        path: 'security', // Route (/security)
        name: 'Security',
        meta: { requiresAuth: true },
        component: SecurityView,
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
  history: createWebHistory('/k-guard/'),
  routes
})

router.beforeEach((to, _from, next) => { 
  const token = localStorage.getItem('user_token');

  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login' });
  } else if (to.name === 'Login' && token) {
    next({ name: 'Health' }); 
  } else {
    next();
  }
});

export default router