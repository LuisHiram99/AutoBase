<script lang="ts">
  import { page } from "$app/stores";

  import IconHome from "$lib/icons/IconHome.svelte";
  import IconClientes from "$lib/icons/IconClientes.svelte";
  import IconVehiculos from "$lib/icons/IconVehiculos.svelte";
  import IconTrabajos from "$lib/icons/IconTrabajos.svelte";
  import IconBitacora from "$lib/icons/IconBitacora.svelte";
  import IconAjustes from "$lib/icons/IconAjustes.svelte";
  import IconArrowDown from "$lib/icons/IconArrowDown.svelte";

  export let user;

  let openDropdown: string | null = null;

  function toggleDropdown(id: string) {
    openDropdown = openDropdown === id ? null : id;
  }

  const activeClass = "bg-gray-700 text-white font-semibold";
</script>

<aside
  id="default-sidebar"
  class="fixed top-0 left-0 z-40 w-49 h-screen transition-transform -translate-x-full sm:translate-x-0"
  aria-label="Sidebar"
>
  <div class="overflow-y-auto py-5 px-3 h-full border-r bg-gray-800 border-gray-700">
    <a
      href="/cuenta"
      class="block p-4 mb-6 rounded-lg cursor-pointer
              hover:bg-gray-600 transition-colors"
    >
      <div class="flex items-center gap-3">
        <div class="w-13 h-13 rounded-full border flex items-center justify-center bg-gray-50">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="35"
            height="35"
            fill="#ccc"
            viewBox="0 0 24 24"
          >
            <path
              d="M12 12c2.761 0 5-2.239 5-5s-2.239-5-5-5-5 2.239-5 5 2.239 5 5 5zm0 2c-3.866 0-7 2.239-7 5v1h14v-1c0-2.761-3.134-5-7-5z"
            />
          </svg>
        </div>

        <div class="leading-tight">
          <p class="font-semibold text-white">
            {user?.first_name}
            {user?.last_name}
          </p>
          <p class="text-xs text-gray-300 capitalize">
            {user?.role}
          </p>
          <p class="text-md text-gray-400">
            Admin {user?.workshop_id}
          </p>
        </div>
      </div>
    </a>

    <hr class="border-gray-700 mb-4" />

    <!-- ======================================= -->
    <!-- MENU PRINCIPAL                         -->
    <!-- ======================================= -->
    <ul class="space-y-2">
      <!-- Inicio -->
      <li>
        <a
          href="/"
          data-sveltekit-preload-data="off"
          class="flex items-center p-2 rounded-lg text-white hover:bg-gray-700 transition
		  {$page.url.pathname === '/' ? 'bg-gray-700 font-semibold' : 'text-white'}"
        >
          <IconHome />
          <span class="ml-3">General</span>
        </a>
      </li>

      <!-- Clientes -->
      <li>
        <a
          href="/clientes"
          data-sveltekit-preload-data="off"
          class="flex items-center p-2 rounded-lg text-white hover:bg-gray-700 transition
		  {$page.url.pathname.startsWith('/clientes') ? 'bg-gray-700 font-semibold' : 'text-white'}"
        >
          <IconClientes />
          <span class="ml-3">Clientes</span>
        </a>
      </li>

      <!-- Vehiculos -->
      <li>
        <a
          href="/vehiculos"
          data-sveltekit-preload-data="off"
          class="flex items-center p-2 rounded-lg text-white hover:bg-gray-700 transition
		  {$page.url.pathname.startsWith('/vehiculos') ? 'bg-gray-700 font-semibold' : 'text-white'}"
        >
          <IconVehiculos />
          <span class="ml-3">Vehículos</span>
        </a>
      </li>

      <!-- Piezas -->
      <li>
        <a
          href="/piezas"
          data-sveltekit-preload-data="off"
          class="flex items-center p-2 rounded-lg text-white hover:bg-gray-700 transition
		  {$page.url.pathname.startsWith('/piezas') ? 'bg-gray-700 font-semibold' : 'text-white'}"
        >
          <IconVehiculos />
          <span class="ml-3">Piezas </span>
        </a>
      </li>
    </ul>

    <ul class="pt-5 mt-5 space-y-2 border-t border-gray-700">
      <!-- Trabajos -->
      <li>
        <a
          href="/trabajos"
          data-sveltekit-preload-data="off"
          class="flex items-center p-2 rounded-lg text-white hover:bg-gray-700 transition
		  {$page.url.pathname.startsWith('/trabajos') ? 'bg-gray-700 font-semibold' : 'text-white'}"
        >
          <IconTrabajos />
          <span class="ml-3">Trabajos</span>
        </a>
      </li>

      <!-- Bitacora -->
      <li>
        <a
          href="/bitacora"
          data-sveltekit-preload-data="off"
          class="flex items-center p-2 rounded-lg text-white hover:bg-gray-700 transition
		  {$page.url.pathname.startsWith('/bitacora') ? 'bg-gray-700 font-semibold' : 'text-white'}"
        >
          <IconBitacora />
          <span class="ml-3">Bitácora</span>
        </a>
      </li>

      <!-- AJUSTES -->
      <li class="select-none">
        <button
          on:click={() => toggleDropdown("Ajustes")}
          class="flex items-center justify-between w-full p-2 rounded-lg text-white hover:bg-gray-700 transition-colors"
        >
          <span class="flex items-center gap-2">
            <IconAjustes />
            Ajustes
          </span>

          <svg
            class="w-4 h-4 transition-transform duration-300"
            style="transform: rotate({openDropdown === 'Ajustes' ? '180deg' : '0deg'})"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              fill-rule="evenodd"
              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </button>

        <!-- Dropdown content -->
        <ul
          class="ml-10 mt-1 overflow-hidden transition-all duration-300 ease-in-out text-white"
          style="max-height: {openDropdown === 'Ajustes' ? '300px' : '0px'}"
        >
          <!-- Cuenta -->
          <li>
            <a
              href="/cuenta"
              class="block p-2 rounded hover:bg-gray-700 transition-colors
				{$page.url.pathname.startsWith('/cuenta') ? 'text-blue-400 font-semibold' : 'text-gray-300'}"
            >
              Cuenta
            </a>
          </li>

          <!-- Empleados -->
          <li>
            <a
              href="/empleados"
              class="block p-2 rounded hover:bg-gray-700 transition-colors
				{$page.url.pathname.startsWith('/empleados') ? 'text-blue-400 font-semibold' : 'text-gray-300'}"
            >
              Empleados
            </a>
          </li>

          <!-- Taller -->
          <li>
            <a
              href="/talleres"
              class="block p-2 rounded hover:bg-gray-700 transition-colors
				{$page.url.pathname.startsWith('/talleres') ? 'text-blue-400 font-semibold' : 'text-gray-300'}"
            >
              Taller
            </a>
          </li>
        </ul>
      </li>
    </ul>
  </div>
</aside>
