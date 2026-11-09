import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, getToken, setToken } from "./api";
import type { Profile } from "./types";

interface Ctx {
  profile: Profile | null;
  loading: boolean;
  signIn: (p: Profile) => void;
  signOut: () => void;
}

const ProfileContext = createContext<Ctx>({ profile: null, loading: true, signIn: () => {}, signOut: () => {} });

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(!!getToken());

  useEffect(() => {
    if (!getToken()) return;
    api.me().then(setProfile).catch(() => setToken(null)).finally(() => setLoading(false));
  }, []);

  const signIn = (p: Profile) => { setToken(p.token); setProfile(p); };
  const signOut = () => { setToken(null); setProfile(null); };

  return <ProfileContext.Provider value={{ profile, loading, signIn, signOut }}>{children}</ProfileContext.Provider>;
}

export const useProfile = () => useContext(ProfileContext);
