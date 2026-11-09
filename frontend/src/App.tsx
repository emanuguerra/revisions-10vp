import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";
import { Home } from "./pages/Home";
import { ProfileGate } from "./pages/ProfileGate";
import { ProgressPage } from "./pages/ProgressPage";
import { UnitPage } from "./pages/UnitPage";
import { ProfileProvider, useProfile } from "./profile";

function Shell() {
  const { profile, loading } = useProfile();
  if (loading) return <p className="muted">Chargement…</p>;
  if (!profile) return <ProfileGate />;
  return (
    <div className="wrap">
      <nav className="subjects" aria-label="Navigation">
        <Link to="/" className="brand">Révisions 10e</Link>
        <NavLink to="/" end className="subj">Accueil</NavLink>
        <NavLink to="/progression" className="subj">Ma progression</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/u/:slug" element={<UnitPage />} />
        <Route path="/u/:slug/:tab" element={<UnitPage />} />
        <Route path="/progression" element={<ProgressPage />} />
        <Route path="*" element={<p>Page introuvable. <Link to="/">Retour à l'accueil</Link></p>} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <ProfileProvider>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </ProfileProvider>
  );
}
