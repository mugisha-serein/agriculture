import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { useAuthStore } from './store/authStore';
import { SystemErrorBoundary } from './components/SystemErrorBoundary';

import { LoginPage } from './pages/identity/LoginPage';

import { DiscoveryPage } from './pages/marketplace/DiscoveryPage';

import { RegisterPage } from './pages/identity/RegisterPage';

import { ProfilePage } from './pages/identity/ProfilePage';
import { CreateListingPage } from './pages/marketplace/CreateListingPage';
import { ProductDetailPage } from './pages/marketplace/ProductDetailPage';
import { SellerProductsPage } from './pages/marketplace/SellerProductsPage';
import { ManageCropsPage } from './pages/marketplace/ManageCropsPage';
import { TransactionsPage } from './pages/payments/TransactionsPage';
import { ReviewsPage } from './pages/reputation/ReviewsPage';

// Lazy load feature pages
import { OrderHistoryPage } from './pages/orders/OrderHistoryPage';
import { OrderDetailPage } from './pages/orders/OrderDetailPage';
import { ShipmentListPage } from './pages/logistics/ShipmentListPage';
import { ShipmentTrackingPage } from './pages/logistics/ShipmentTrackingPage';

const ProtectedRoute = ({ children, allowedRoles }: { children: React.ReactNode, allowedRoles?: string[] }) => {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) return <Navigate to="/login" />;

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // Redirect based on role to their dashboard
    if (user.role === 'seller') return <Navigate to="/products/me" />;
    if (user.role === 'transporter') return <Navigate to="/shipments" />;
    return <Navigate to="/" />;
  }

  // Mandatory verification for sellers and transporters
  if (user && (user.role === 'seller' || user.role === 'transporter') && !user.is_verified) {
    // Verification is managed directly inside profile.
    if (window.location.pathname !== '/profile') {
      return <Navigate to="/profile" />;
    }
  }

  return <>{children}</>;
};

const MarketplaceAccessRoute = ({ children, allowSellers = false }: { children: React.ReactNode, allowSellers?: boolean }) => {
  const { user } = useAuthStore();

  // Guests and buyers can always access
  if (!user || user.role === 'buyer') return <>{children}</>;

  // Sellers are allowed if specifically permitted (e.g. for product details)
  if (user.role === 'seller' && allowSellers) return <>{children}</>;

  // Otherwise redirect to dashboard
  if (user.role === 'seller') return <Navigate to="/products/me" />;
  if (user.role === 'transporter') return <Navigate to="/shipments" />;
  return <Navigate to="/" />;
};

function App() {
  const { checkAuth } = useAuthStore();

  React.useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <SystemErrorBoundary>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="discovery" element={
              <MarketplaceAccessRoute>
                <DiscoveryPage />
              </MarketplaceAccessRoute>
            } />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="verify-account" element={<Navigate to="/profile" replace />} />

            <Route path="orders" element={
              <ProtectedRoute>
                <OrderHistoryPage />
              </ProtectedRoute>
            } />
            <Route path="orders/:orderId" element={
              <ProtectedRoute>
                <OrderDetailPage />
              </ProtectedRoute>
            } />
            <Route path="shipments" element={
              <ProtectedRoute allowedRoles={['seller', 'transporter']}>
                <ShipmentListPage />
              </ProtectedRoute>
            } />
            <Route path="shipments/:shipmentId" element={
              <ProtectedRoute allowedRoles={['seller', 'transporter', 'buyer']}>
                <ShipmentTrackingPage />
              </ProtectedRoute>
            } />
            <Route path="profile" element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } />
            <Route path="transactions" element={
              <ProtectedRoute>
                <TransactionsPage />
              </ProtectedRoute>
            } />
            <Route path="reputation/:userId" element={
              <ProtectedRoute>
                <ReviewsPage />
              </ProtectedRoute>
            } />
            <Route path="products/me" element={
              <ProtectedRoute allowedRoles={['seller']}>
                <SellerProductsPage />
              </ProtectedRoute>
            } />
            <Route path="products/:productId" element={
              <MarketplaceAccessRoute allowSellers={true}>
                <ProductDetailPage />
              </MarketplaceAccessRoute>
            } />
            <Route path="products/create" element={
              <ProtectedRoute allowedRoles={['seller']}>
                <CreateListingPage />
              </ProtectedRoute>
            } />
            <Route path="seller/crops" element={
              <ProtectedRoute allowedRoles={['seller']}>
                <ManageCropsPage />
              </ProtectedRoute>
            } />
          </Route>
        </Routes>
      </SystemErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
