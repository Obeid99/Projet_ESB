import React from 'react';
import {
  Box,
  Button,
  Flex,
  Icon,
  Image,
  Text,
  useColorModeValue,
} from '@chakra-ui/react';
import { IoArrowBack, IoLogOut } from 'react-icons/io5';
import logo from '/public/img/esb.png';
import { IRoute } from '@/types/navigation'; // Make sure this exists

interface SidebarProps {
  routes: IRoute[];
}

const Sidebar: React.FC<SidebarProps> = ({ routes }) => {
  let sidebarBg = useColorModeValue('white', 'navy.800');
  let sidebarRadius = '14px';
  let sidebarMargins = '0px';

  return (
    <Flex
      direction="column"
      display={{ base: 'none', xl: 'flex' }}
      position="fixed"
      minH="100%"
      justifyContent="space-between"
    >
      <Box
        bg={sidebarBg}
        w="250px"
        my={{ sm: '16px' }}
        h="calc(100vh - 32px)"
        m={sidebarMargins}
        borderRadius={sidebarRadius}
        p="20px"
        display="flex"
        flexDirection="column"
      >
        <Box mb="20px" textAlign="center">
          <Image src={logo.src} alt="Logo" boxSize="100px" mx="auto" />
        </Box>

        {/* Render dynamic nav items */}
        {routes.map((route, idx) => (
          <Button key={idx} variant="ghost" w="full" justifyContent="flex-start">
            <Text>{route.name}</Text>
          </Button>
        ))}

        <Flex flex="1" />
        <Button
          leftIcon={<Icon as={IoLogOut} />}
          variant="solid"
          colorScheme="red"
          w="full"
          mt="auto"
          fontWeight="bold"
          justifyContent="flex-start"
        >
          Logout
        </Button>
      </Box>
    </Flex>
  );
};

export default Sidebar;
