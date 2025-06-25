import MaterialUpload from '../components/MaterialUpload';
import { useAuth } from '../contexts/AuthContext';

export default function Home() {
  const { token } = useAuth();

  if (!token) {
    return <div>Please log in to access this page.</div>;
  }

  return (
    <div className="bg-black min-h-screen flex">
      <div className="flex-1 flex flex-col justify-end items-center px-4 py-32">
        <MaterialUpload />
      </div>
    </div>
  );
}
