'use client';
import { Box, Button, Input, VStack, Text, Flex } from '@chakra-ui/react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = () => {
    if (username && password) {
      localStorage.setItem('authenticated', 'true');
      router.push('/chatbot');
    } else {
      alert('Please enter valid credentials.');
    }
  };

  return (
    <Flex
      w="100vw"
      h="100vh"
      alignItems="center"
      justifyContent="center"
      bg="gray.100"
    >
      <Box
        w="400px"
        bg="white"
        borderRadius="md"
        boxShadow="md"
        p="20px"
        textAlign="center"
      >
        <Text fontSize="xl" fontWeight="bold" mb="20px">
          Login
        </Text>
        <VStack spacing="10px">
          <Input
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <Input
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button colorScheme="red" w="100%" onClick={handleLogin}>
            Login
          </Button>
        </VStack>
      </Box>
    </Flex>
  );
}
