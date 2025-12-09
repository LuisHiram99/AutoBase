<script lang="ts">
  export let form: any;
  export let data: { message?: string | null };
</script>

<section class="bg-[#FFFFFF] min-h-screen flex items-center">
  <div
    class="flex flex-col items-center justify-center px-6 py-8 mx-auto w-full md:h-screen lg:py-0"
  >
    <span class="text-3xl font-semibold text-gray-900">Los Chinos</span>

    <!-- Card -->
    <div class="w-full bg-white rounded-lg shadow-2xl sm:max-w-md xl:p-0">
      <div class="p-6 space-y-4 md:space-y-6 sm:p-8">
        <h1 class="text-xl font-bold leading-tight tracking-tight text-gray-900 md:text-2xl">
          Iniciar sesión
        </h1>

        <!-- Mensaje desde load() -->
        {#if data?.message}
          <p class="text-sm text-amber-600">{data.message}</p>
        {/if}

        <!-- Mensaje de error del action -->
        {#if form?.error}
          <p class="text-sm text-red-600">{form.error}</p>
        {/if}

        <!-- FORMULARIO -->
        <form method="POST" class="space-y-4 md:space-y-6">
          <!-- Email -->
          <div>
            <label for="username" class="block mb-2 text-sm font-medium text-gray-900">
              Correo electrónico
            </label>
            <input
              type="email"
              name="username"
              id="username"
              required
              placeholder="tucorreo@gmail.com"
              value={form?.values?.email ?? ""}
              class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg
                     focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5
                     "
            />
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block mb-2 text-sm font-medium text-gray-900">
              Contraseña
            </label>
            <input
              type="password"
              name="password"
              id="password"
              required
              placeholder="••••••••"
              class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg
                     focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5
                     "
            />
          </div>

          <!-- Opciones -->
          <div class="flex items-center justify-between">
            <div class="flex items-start">
              <div class="flex items-center h-5">
                <input
                  id="remember"
                  type="checkbox"
                  class="w-4 h-4 border border-gray-300 rounded bg-gray-50
                         focus:ring-3 focus:ring-blue-300
                         "
                />
              </div>
              <label for="remember" class="ml-3 text-sm text-gray-500"> Recordarme </label>
            </div>

            <a href="#" class="text-sm font-medium text-blue-600 hover:underline">
              ¿Olvidaste tu contraseña?
            </a>
          </div>

          <!-- Botón -->
          <button
            type="submit"
            class="w-full text-white bg-[#3490DC] hover:bg-[#227DC7]
                   focus:ring-4 focus:outline-none focus:ring-blue-300
                   font-medium rounded-lg text-sm px-5 py-2.5 text-center
                   "
          >
            Entrar
          </button>
        </form>
      </div>
    </div>
  </div>
</section>
