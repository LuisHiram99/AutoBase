// @ts-nocheck
// src/routes/login/+page.server.ts
import type { Actions, PageServerLoad } from './$types';
import { fail, redirect } from '@sveltejs/kit';
import { PUBLIC_API_BASE_URL } from '$env/static/public';

export const load = async ({ locals, url }: Parameters<PageServerLoad>[0]) => {
  // Si ya está logueado, no tiene sentido ver el login
  if (locals.user) {
    throw redirect(303, '/');
  }

  const reason = url.searchParams.get('reason');
  let message: string | null = null;

  if (reason === 'unauthorized') {
    message = 'No tienes permiso para acceder a esa sección.';
  }

  return {
    message
  };
};

export const actions = {
  default: async ({ request, cookies }: import('./$types').RequestEvent) => {
    const formData = await request.formData();
    const email = String(formData.get('username') ?? '');
    const password = String(formData.get('password') ?? '');

    if (!email || !password) {
      return fail(400, {
        error: 'Correo y contraseña son obligatorios.',
        values: { email }
      });
    }

    // 🔹 Solo envolvemos el fetch en try/catch
    let data: { access_token: string; token_type: string };

    try {
      const body = new URLSearchParams();
      body.append('grant_type', 'password');
      body.append('username', email); // el backend espera "username" pero es el email
      body.append('password', password);
      body.append('scope', '');
      body.append('client_id', 'string');
      body.append('client_secret', 'string'); // ajusta si tu backend no lo necesita

      const res = await fetch(`${PUBLIC_API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body
      });

      if (!res.ok) {
        return fail(res.status, {
          error: 'Credenciales inválidas o error al iniciar sesión...',
          values: { email }
        });
      }

      data = await res.json();
    } catch (err) {
      console.error('Error en login:', err);
      return fail(500, {
        error: 'No se pudo conectar con el servidor.',
        values: { email }
      });
    }

    // 🔹 Esto ya va FUERA del try/catch, para NO atrapar el redirect
    cookies.set('access_token', data.access_token, {
      path: '/',
      httpOnly: true,
      sameSite: 'lax',
      secure: false // ponlo en true cuando uses HTTPS en producción
      // maxAge: 60 * 60 // opcional: 1 hora
    });

    throw redirect(303, '/');
  }
};

;null as any as Actions;