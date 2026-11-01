import { useQuery } from '@tanstack/react-query'
import { getData } from '../lib/api'

export function usePermissions() {
  return useQuery({
    queryKey: ['permissions'],
    queryFn: () => getData<string[]>('/auth/permissions'),
  })
}
