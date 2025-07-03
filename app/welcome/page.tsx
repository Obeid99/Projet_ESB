'use client';
import { Box, Button, Flex, Text, VStack } from '@chakra-ui/react';
import { useRouter } from 'next/navigation';

export default function WelcomePage() {
  const router = useRouter();

  return (
    <Box w="100vw" h="100vh" position="relative" overflow="hidden">
      {/* Background flou */}
      <Box
        position="absolute"
        top={0}
        left={0}
        right={0}
        bottom={0}
        bgImage="url('/img/ESB-1.jpg')"
        bgSize="cover"
        bgPosition="center"
        filter="blur(8px)"
        zIndex={0}
      />

      {/* Contenu principal */}
      <Flex
        position="relative"
        zIndex={1}
        w="100%"
        h="100%"
        alignItems="center"
        justifyContent="center"
      >
        <Box
          w="400px"
          bg="red.500"
          borderRadius="md"
          boxShadow="lg"
          p="20px"
          textAlign="center"
        >
          <Text fontSize="2xl" fontWeight="bold" mb="20px" color="white">
            Welcome to Chatbot-ESB
          </Text>
          <VStack spacing="10px">
            <Button
              colorScheme="whiteAlpha"
              variant="outline"
              _hover={{ bg: 'white', color: 'black' }}
              onClick={() => router.push('/login?redirect=chatbot')}
            >
              Student
            </Button>
            <Button
              colorScheme="whiteAlpha"
              variant="outline"
              _hover={{ bg: 'white', color: 'black' }}
              onClick={() => router.push('/login?redirect=administration-chatbot')}
            >
              Administration
            </Button>
          </VStack>
        </Box>
      </Flex>
    </Box>
  );
}
