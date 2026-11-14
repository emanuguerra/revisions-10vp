import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";
import { Home } from "./pages/Home";
import { ProfileGate } from "./pages/ProfileGate";
import { ProgressPage } from "./pages/ProgressPage";
import { UnitPage } from "./pages/UnitPage";
import { AccessGate } from "./access";
import { FocusControl, FocusProvider } from "./focus";
import { ProfileProvider, useProfile } from "./profile";
import { RewardsProvider, XpChip } from "./rewards";

function Shell() {
  const { profile, loading } = useProfile();
  if (loading) return <p className="muted">Chargement…</p>;
  if (!profile) return <ProfileGate />;
  return (
    <RewardsProvider>
    <FocusProvider>
    <div className="wrap">
      <nav className="subjects" aria-label="Navigation">
        <Link to="/" className="brand">Révisions 10e</Link>
        <NavLink to="/" end className="subj">Accueil</NavLink>
        <NavLink to="/progression" className="subj">Ma progression</NavLink>
        <FocusControl />
        <XpChip />
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/u/:slug" element={<UnitPage />} />
        <Route path="/u/:slug/:tab" element={<UnitPage />} />
        <Route path="/progression" element={<ProgressPage />} />
        <Route path="*" element={<p>Page introuvable. <Link to="/">Retour à l'accueil</Link></p>} />
      </Routes>
    </div>
    </FocusProvider>
    </RewardsProvider>
  );
}

export default function App() {
  return (
    <AccessGate>
      <ProfileProvider>
        <BrowserRouter>
          <Shell />
        </BrowserRouter>
      </ProfileProvider>
    </AccessGate>
  );
}
