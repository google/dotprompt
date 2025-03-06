import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import App from './app';

// Define the routes
export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
  },
  {
    path: '/:fiddleId',
    element: <App />,
  },
  {
    path: '/:fiddleId/:promptName',
    element: <App />,
  },
]);

// Export the RouterProvider component
export function Router() {
  return <RouterProvider router={router} />;
}
