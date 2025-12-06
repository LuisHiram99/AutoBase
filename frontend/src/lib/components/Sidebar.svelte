<script lang="ts">
  import { page } from "$app/stores";

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
    <ul class="space-y-2">
      <!-- Inicio -->
      <li>
        <a
          href="/"
          data-sveltekit-preload-data="off"
          class="flex items-center p-2 rounded-lg text-white hover:bg-gray-700 transition
		  {$page.url.pathname === '/' ? 'bg-gray-700 font-semibold' : 'text-white'}"
        >
          <svg
            aria-hidden="true"
            class="w-6 h-6 text-gray-400 transition duration-75 group-hover: group-hover:text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
            ><path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z"></path><path
              d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z"
            ></path></svg
          >
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
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#99a1af"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="icon icon-tabler icons-tabler-outline icon-tabler-users"
            ><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><path
              d="M9 7m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0"
            ></path><path d="M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2"></path><path
              d="M16 3.13a4 4 0 0 1 0 7.75"
            ></path><path d="M21 21v-2a4 4 0 0 0 -3 -3.85"></path></svg
          >
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
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="#99a1af"
            class="icon icon-tabler icons-tabler-filled icon-tabler-car"
            ><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><path
              d="M14 5a1 1 0 0 1 .694 .28l.087 .095l3.699 4.625h.52a3 3 0 0 1 2.995 2.824l.005 .176v4a1 1 0 0 1 -1 1h-1.171a3.001 3.001 0 0 1 -5.658 0h-4.342a3.001 3.001 0 0 1 -5.658 0h-1.171a1 1 0 0 1 -1 -1v-6l.007 -.117l.008 -.056l.017 -.078l.012 -.036l.014 -.05l2.014 -5.034a1 1 0 0 1 .928 -.629zm-7 11a1 1 0 1 0 0 2a1 1 0 0 0 0 -2m10 0a1 1 0 1 0 0 2a1 1 0 0 0 0 -2m-6 -9h-5.324l-1.2 3h6.524zm2.52 0h-.52v3h2.92z"
            ></path></svg
          >
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
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="#99a1af"
            class="icon icon-tabler icons-tabler-filled icon-tabler-car"
            ><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><path
              d="M14 5a1 1 0 0 1 .694 .28l.087 .095l3.699 4.625h.52a3 3 0 0 1 2.995 2.824l.005 .176v4a1 1 0 0 1 -1 1h-1.171a3.001 3.001 0 0 1 -5.658 0h-4.342a3.001 3.001 0 0 1 -5.658 0h-1.171a1 1 0 0 1 -1 -1v-6l.007 -.117l.008 -.056l.017 -.078l.012 -.036l.014 -.05l2.014 -5.034a1 1 0 0 1 .928 -.629zm-7 11a1 1 0 1 0 0 2a1 1 0 0 0 0 -2m10 0a1 1 0 1 0 0 2a1 1 0 0 0 0 -2m-6 -9h-5.324l-1.2 3h6.524zm2.52 0h-.52v3h2.92z"
            ></path></svg
          >
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
          <svg
            aria-hidden="true"
            class="shrink-0 w-6 h-6 transition duration-75 text-gray-400 group-hover: group-hover:text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
            ><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"></path><path
              fill-rule="evenodd"
              d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z"
              clip-rule="evenodd"
            ></path></svg
          >
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
          <svg
            aria-hidden="true"
            class="shrink-0 w-6 h-6 transition duration-75 text-gray-400 group-hover: group-hover:text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
            ><path
              d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"
            ></path></svg
          >
          <span class="ml-3">Bitácora</span>
        </a>
      </li>

      <li>
        <button
          on:click={() => toggleDropdown("Ajustes")}
          class="flex items-center justify-between w-full p-2 rounded-lg text-white hover:bg-gray-700"
        >
          <span class="flex items-center gap-2">
            <svg
              aria-hidden="true"
              class="shrink-0 w-6 h-6 text-gray-400 transition duration-75 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
              xmlns="http://www.w3.org/2000/svg"
              ><path
                fill-rule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-2 0c0 .993-.241 1.929-.668 2.754l-1.524-1.525a3.997 3.997 0 00.078-2.183l1.562-1.562C15.802 8.249 16 9.1 16 10zm-5.165 3.913l1.58 1.58A5.98 5.98 0 0110 16a5.976 5.976 0 01-2.516-.552l1.562-1.562a4.006 4.006 0 001.789.027zm-4.677-2.796a4.002 4.002 0 01-.041-2.08l-.08.08-1.53-1.533A5.98 5.98 0 004 10c0 .954.223 1.856.619 2.657l1.54-1.54zm1.088-6.45A5.974 5.974 0 0110 4c.954 0 1.856.223 2.657.619l-1.54 1.54a4.002 4.002 0 00-2.346.033L7.246 4.668zM12 10a2 2 0 11-4 0 2 2 0 014 0z"
                clip-rule="evenodd"
              ></path></svg
            >
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

        <ul
          class="pl-11 space-y-2 overflow-hidden transition-[max-height] duration-300 ease-out text-white"
          style="max-height: {openDropdown === 'Ajustes' ? '250px' : '0'}"
        >
          <li>
            <a
              href="/cuenta"
              data-sveltekit-preload-data="off"
              class="block p-2 rounded-lg hover:text-blue-600
              {$page.url.pathname.startsWith('/cuenta')
                ? 'bg-gray-700 font-semibold'
                : 'text-white'}">Cuenta</a
            >
          </li>
          <li>
            <a
              href="/empleados"
              data-sveltekit-preload-data="off"
              class="block p-2 rounded-lg hover:text-blue-600
              {$page.url.pathname.startsWith('/empleados')
                ? 'bg-gray-700 font-semibold'
                : 'text-white'}">Empleados</a
            >
          </li>
          <li>
            <a
              href="/talleres"
              data-sveltekit-preload-data="off"
              class="block p-2 rounded-lg hover:text-blue-600
              {$page.url.pathname.startsWith('/taller')
                ? 'bg-gray-700 font-semibold'
                : 'text-white'}">Taller</a
            >
          </li>
        </ul>
      </li>
    </ul>
  </div>
</aside>
