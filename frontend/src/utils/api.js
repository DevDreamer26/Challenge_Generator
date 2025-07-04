import {useAuth} from "@clerk/clerk-react"


export const useApi = () =>{
    const {getToken} = useAuth()

    const makeRequest =  async(endpoint, options= {}) => {
        const token = await getToken()
        const defaultoptions = {
            headers: {
                "content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            }
        }

        const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/${endpoint}`,{
            ...defaultoptions,
            ...options
        })

        if (!response.ok){
            const errorData = await response.json().catch(()=>null)
            if (response.status===429){
                throw new Error("Daily quota exceeded")
            }
            throw new Error(errorData?.detail || "An error occured")
        }

        return await response.json()
    }
    return {makeRequest}
}

