// Simple view router for the SCLAPP SPA: maps view id (e.g. 'dashboard', 'companies') to a render function.
// initRouter() stores the main content element and the route map; navigateTo(viewId) renders the view into main.

let routes = {};
let mainElement = null;

export function initRouter({ mainElement: element, routes: routesMap }) {
  mainElement = element;
  routes = routesMap || {};
}

export function navigateTo(viewId) {
  if (!mainElement) return;
  const render = routes[viewId];
  if (typeof render === 'function') {
    render(mainElement);
  }
}

