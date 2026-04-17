import React, { createContext, useContext, useState } from 'react'

interface ApiConfig {
  model: string
  temperature: number
  setModel: (m: string) => void
  setTemperature: (t: number) => void
}

const ApiContext = createContext<ApiConfig>({
  model: 'gpt-5.4',
  temperature: 0.7,
  setModel: () => {},
  setTemperature: () => {},
})

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const [model, setModel] = useState('gpt-5.4')
  const [temperature, setTemperature] = useState(0.7)

  return (
    <ApiContext.Provider value={{ model, temperature, setModel, setTemperature }}>
      {children}
    </ApiContext.Provider>
  )
}

export function useApiConfig() {
  return useContext(ApiContext)
}
