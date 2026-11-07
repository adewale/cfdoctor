function render(config) { const zone = config.route.split('/')[0].split('.').slice(-2).join('.'); return {routes:[{pattern:config.route,zone_name:zone}]}; }
